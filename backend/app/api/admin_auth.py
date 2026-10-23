import secrets as pysecrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core import security
from ..core.config import get_settings
from ..core.db import get_db
from ..models import AdminUser, RefreshToken
from .deps import (ACCESS_COOKIE, ADMIN_HEADER, REFRESH_COOKIE, RateLimiter, admin_required, admin_session_required,
                   client_ip, is_https)

router = APIRouter(prefix="/api/v1/admin/auth", tags=["admin-auth"])
login_limiter = RateLimiter(8, 900)


class LoginBody(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=256)


class PasswordBody(BaseModel):
    current_password: str = Field(max_length=256)
    new_password: str = Field(min_length=10, max_length=256)


def _secure(request: Request) -> bool:
    mode = get_settings().cookie_secure.lower()
    if mode in ("true", "1", "yes"):
        return True
    if mode in ("false", "0", "no"):
        return False
    # Believing a forged "https" only ever makes the cookie stricter, so this header is safe to honour even
    # when the proxy is not formally trusted.
    forwarded = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    return is_https(request) or forwarded == "https"


def _set_cookies(request: Request, response: Response, user: AdminUser, refresh: str) -> None:
    s = get_settings()
    access, _ = security.create_access_jwt(user.id, user.username)
    kw = dict(httponly=True, secure=_secure(request), samesite="strict")
    response.set_cookie(ACCESS_COOKIE, access, max_age=s.access_token_minutes * 60, path="/api/v1/admin", **kw)
    response.set_cookie(REFRESH_COOKIE, refresh, max_age=s.refresh_token_days * 86400,
                        path="/api/v1/admin/auth", **kw)


def _clear_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/api/v1/admin")
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/admin/auth")


def _issue_refresh(db: Session, request: Request, user: AdminUser, family: str | None = None) -> str:
    s = get_settings()
    raw = security.new_token(32)
    db.add(RefreshToken(
        user_id=user.id, family_id=family or pysecrets.token_hex(8), token_hash=security.sha256_hex(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=s.refresh_token_days),
        ip=client_ip(request), user_agent=(request.headers.get("user-agent") or "")[:200],
    ))
    db.flush()
    return raw


def _csrf(request: Request) -> None:
    if request.headers.get(ADMIN_HEADER) != "1":
        raise HTTPException(403, "Cabecera de seguridad ausente")


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(get_db)):
    _csrf(request)
    key = client_ip(request)
    if not login_limiter.check(key):
        raise HTTPException(429, "Demasiados intentos. Espera unos minutos.")
    user = db.query(AdminUser).filter(AdminUser.username == body.username).one_or_none()
    # Verify against a dummy hash for unknown users so timing does not reveal them.
    ok = security.verify_password(user.password_hash if user else _DUMMY_HASH, body.password)
    if not user or not ok:
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    login_limiter.reset(key)
    raw = _issue_refresh(db, request, user)
    _set_cookies(request, response, user, raw)
    return {"username": user.username, "must_change_password": user.must_change_password}


_DUMMY_HASH = security.hash_password("homehq-dummy-password")


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    _csrf(request)
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise HTTPException(401, "Sin sesión")
    row = db.query(RefreshToken).filter(RefreshToken.token_hash == security.sha256_hex(raw)).one_or_none()
    now = datetime.now(timezone.utc)
    if not row:
        _clear_cookies(response)
        raise HTTPException(401, "Sesión no válida")
    if row.used_at or row.revoked_at:
        # A rotated token came back: assume theft and kill every token of the family.
        db.query(RefreshToken).filter(RefreshToken.family_id == row.family_id, RefreshToken.revoked_at.is_(None)) \
            .update({"revoked_at": now})
        db.commit()
        _clear_cookies(response)
        raise HTTPException(401, "Sesión revocada por reutilización de token")
    exp = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=timezone.utc)
    if exp < now:
        _clear_cookies(response)
        raise HTTPException(401, "Sesión caducada")
    user = db.get(AdminUser, row.user_id)
    if not user:
        _clear_cookies(response)
        raise HTTPException(401, "Sesión no válida")
    row.used_at = now
    new_raw = _issue_refresh(db, request, user, family=row.family_id)
    _set_cookies(request, response, user, new_raw)
    return {"username": user.username, "must_change_password": user.must_change_password}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    _csrf(request)
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        row = db.query(RefreshToken).filter(RefreshToken.token_hash == security.sha256_hex(raw)).one_or_none()
        if row:
            db.query(RefreshToken).filter(RefreshToken.family_id == row.family_id) \
                .update({"revoked_at": datetime.now(timezone.utc)})
    _clear_cookies(response)
    return {"ok": True}


@router.get("/me")
def me(user: AdminUser = Depends(admin_required)):
    return {"username": user.username, "must_change_password": user.must_change_password}


@router.post("/password")
def change_password(body: PasswordBody, request: Request, response: Response,
                    user: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    if not security.verify_password(user.password_hash, body.current_password):
        raise HTTPException(400, "La contraseña actual no es correcta")
    user.password_hash = security.hash_password(body.new_password)
    user.must_change_password = False
    # Force every other session to log in again.
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)) \
        .update({"revoked_at": datetime.now(timezone.utc)})
    raw = _issue_refresh(db, request, user)
    _set_cookies(request, response, user, raw)
    # The generated first-run password is useless after this and must not linger on disk.
    (get_settings().secrets_dir / "initial-admin-password.txt").unlink(missing_ok=True)
    return {"ok": True}
