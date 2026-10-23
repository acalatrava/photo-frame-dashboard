import time
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core import security
from ..core.config import get_settings
from ..core.db import get_db
from ..models import AdminUser, ApiToken, Device

ACCESS_COOKIE = "hq_access"
REFRESH_COOKIE = "hq_refresh"
ADMIN_HEADER = "x-homehq-admin"


def client_ip(request: Request) -> str:
    if get_settings().trust_proxy:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "?"


def is_https(request: Request) -> bool:
    if request.url.scheme == "https":
        return True
    return get_settings().trust_proxy and request.headers.get("x-forwarded-proto") == "https"


API_TOKEN_PREFIX = "hqa_"
_token_failures = None  # created below, after RateLimiter is defined


def _as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _api_token_user(request: Request, db: Session, raw: str, enforce_scope: bool = True) -> AdminUser:
    """Authenticate `Authorization: Bearer hqa_...`. Read tokens may only use safe methods unless the caller
    enforces scope itself (the MCP endpoint does, per tool)."""
    ip = client_ip(request)
    if not _token_failures.check(ip):
        raise HTTPException(429, "Demasiados intentos con un token no válido")
    row = db.query(ApiToken).filter(ApiToken.token_hash == security.sha256_hex(raw)).one_or_none() \
        if raw.startswith(API_TOKEN_PREFIX) else None
    now = datetime.now(timezone.utc)
    if not row or row.revoked_at or (row.expires_at and _as_utc(row.expires_at) < now):
        raise HTTPException(401, "Token no válido, revocado o caducado", headers={"WWW-Authenticate": "Bearer"})
    _token_failures.reset(ip)
    if enforce_scope and row.scope != "full" and request.method not in ("GET", "HEAD", "OPTIONS"):
        raise HTTPException(403, "Este token es de solo lectura")
    user = db.get(AdminUser, row.user_id)
    if not user:
        raise HTTPException(401, "Token no válido")
    if not row.last_used_at or (now - _as_utc(row.last_used_at)).total_seconds() > 60:
        row.last_used_at = now
        db.commit()
    request.state.api_token = row
    return user


def admin_session_required(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    """Browser session only (cookie). Used for things an API token must never do, like minting tokens."""
    # SameSite=Strict already blocks cross-site cookies; the custom header is a second barrier.
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get(ADMIN_HEADER) != "1":
        raise HTTPException(403, "Cabecera de seguridad ausente")
    token = request.cookies.get(ACCESS_COOKIE)
    data = security.decode_access_jwt(token) if token else None
    if not data:
        raise HTTPException(401, "No autenticado")
    user = db.get(AdminUser, int(data["sub"]))
    if not user:
        raise HTTPException(401, "No autenticado")
    return user


def admin_required(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    """Admin access by browser session or by an API token."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return _api_token_user(request, db, auth[7:].strip())
    return admin_session_required(request, db)


def mcp_token_user(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    """Bearer API token only (never a cookie). Scope is applied later, call by call, by the admin API itself."""
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Se necesita un token de API (Authorization: Bearer hqa_...)",
                            headers={"WWW-Authenticate": "Bearer"})
    return _api_token_user(request, db, auth[7:].strip(), enforce_scope=False)


_last_seen_write: dict[str, float] = {}


def device_required(request: Request, db: Session = Depends(get_db)) -> Device:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Token de dispositivo requerido")
    h = security.sha256_hex(auth[7:].strip())
    device = db.query(Device).filter(Device.token_hash == h).one_or_none()
    if not device or device.status != "active":
        raise HTTPException(401, "Dispositivo no autorizado")
    now = time.time()
    if now - _last_seen_write.get(device.id, 0) > 20:
        _last_seen_write[device.id] = now
        device.last_seen_at = datetime.now(timezone.utc)
        device.last_ip = client_ip(request)
        db.commit()
    return device


class RateLimiter:
    """Tiny in-memory sliding window limiter (single process)."""

    def __init__(self, limit: int, window_s: int):
        self.limit, self.window = limit, window_s
        self.hits: dict[str, list[float]] = {}

    def check(self, key: str) -> bool:
        now = time.time()
        arr = [t for t in self.hits.get(key, []) if now - t < self.window]
        ok = len(arr) < self.limit
        if ok:
            arr.append(now)
        self.hits[key] = arr
        return ok

    def reset(self, key: str) -> None:
        self.hits.pop(key, None)


_token_failures = RateLimiter(30, 900)
