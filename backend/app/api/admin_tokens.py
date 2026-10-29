from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core import security
from ..core.db import get_db
from ..models import AdminUser, ApiToken
from .deps import API_TOKEN_PREFIX, admin_session_required

# A `trigger` token can only fire actions on the frames (see trigger.py); it is meant for Home Assistant.
# Minting and revoking tokens needs a real login: a token can never create more tokens.
router = APIRouter(prefix="/api/v1/admin/tokens", tags=["admin-tokens"])
MAX_ACTIVE = 20


class TokenBody(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    scope: str = Field("read", pattern="^(read|full|trigger)$")
    expires_days: int | None = Field(None, ge=1, le=3650)


def _dict(t: ApiToken) -> dict:
    return {"id": t.id, "name": t.name, "prefix": t.prefix, "scope": t.scope,
            "created_at": t.created_at.isoformat(),
            "expires_at": t.expires_at.isoformat() if t.expires_at else None,
            "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
            "revoked": bool(t.revoked_at)}


@router.get("")
def list_tokens(user: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    rows = db.query(ApiToken).filter(ApiToken.user_id == user.id).order_by(ApiToken.created_at.desc()).all()
    return [_dict(t) for t in rows]


@router.post("")
def create_token(body: TokenBody, user: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    active = db.query(ApiToken).filter(ApiToken.user_id == user.id, ApiToken.revoked_at.is_(None)).count()
    if active >= MAX_ACTIVE:
        raise HTTPException(400, f"Ya hay {MAX_ACTIVE} tokens activos; revoca alguno")
    raw = API_TOKEN_PREFIX + security.new_token(32)
    row = ApiToken(user_id=user.id, name=body.name.strip(), token_hash=security.sha256_hex(raw), prefix=raw[:10],
                   scope=body.scope,
                   expires_at=datetime.now(timezone.utc) + timedelta(days=body.expires_days) if body.expires_days else None)
    db.add(row)
    db.flush()
    # The only time the token is ever shown.
    return {**_dict(row), "token": raw}


@router.delete("/{token_id}")
def revoke_token(token_id: int, user: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    row = db.get(ApiToken, token_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "Token no encontrado")
    row.revoked_at = datetime.now(timezone.utc)
    return {"ok": True}
