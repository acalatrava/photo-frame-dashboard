"""Password hashing, token helpers and the encrypted secret store."""
import base64
import hashlib
import hmac
import os
import secrets as pysecrets
import time
from pathlib import Path

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from .config import get_settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def new_token(nbytes: int = 32) -> str:
    return pysecrets.token_urlsafe(nbytes)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def constant_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


def _write_secret_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)


def master_key() -> bytes:
    """32 url-safe base64 bytes used as the Fernet key; never leaves the server."""
    s = get_settings()
    if s.secret_key:
        return s.secret_key.encode()
    path = s.secrets_dir / "master.key"
    if not path.exists():
        _write_secret_file(path, Fernet.generate_key())
    return path.read_bytes().strip()


def _fernet() -> Fernet:
    return Fernet(master_key())


def derive_key(purpose: str) -> bytes:
    return hmac.new(base64.urlsafe_b64decode(master_key()), purpose.encode(), hashlib.sha256).digest()


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str | None:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return None


def create_access_jwt(user_id: int, username: str) -> tuple[str, int]:
    s = get_settings()
    now = int(time.time())
    exp = now + s.access_token_minutes * 60
    payload = {"sub": str(user_id), "usr": username, "iat": now, "exp": exp, "typ": "access", "jti": new_token(8)}
    return jwt.encode(payload, derive_key("jwt"), algorithm="HS256"), exp


def decode_access_jwt(token: str) -> dict | None:
    try:
        data = jwt.decode(token, derive_key("jwt"), algorithms=["HS256"], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        return None
    return data if data.get("typ") == "access" else None


def media_signature(device_secret: str, path: str) -> str:
    """Stable capability signature for media URLs, so <img src> works without headers and caches."""
    return hmac.new(device_secret.encode(), path.encode(), hashlib.sha256).hexdigest()[:32]
