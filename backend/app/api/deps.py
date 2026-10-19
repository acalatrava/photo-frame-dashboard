import time
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core import security
from ..core.config import get_settings
from ..core.db import get_db
from ..models import AdminUser, Device

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


def admin_required(request: Request, db: Session = Depends(get_db)) -> AdminUser:
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
