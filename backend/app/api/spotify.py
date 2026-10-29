"""Spotify: linking the account from the panel, and the controls the frames use."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models import AdminUser, Device
from ..services import config_service
from ..services.spotify import service as sp
from .deps import RateLimiter, admin_required, admin_session_required, device_required

admin = APIRouter(prefix="/api/v1/admin/spotify", tags=["spotify"])
frame = APIRouter(prefix="/api/v1/device/music", tags=["music"])
limiter = RateLimiter(90, 60)


def _cfg(db: Session):
    g, _ = config_service.get_global(db)
    return g.spotify


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except sp.SpotifyError as e:
        raise HTTPException(e.status, e.message)


def _ready(db: Session) -> str:
    cfg = _cfg(db)
    if not cfg.enabled or not cfg.client_id or not sp.connected():
        raise HTTPException(409, "Spotify no está conectado")
    return cfg.client_id


# ------------------------------------------------------------------ panel
class CodeBody(BaseModel):
    code: str = Field(min_length=6, max_length=2000)


@admin.get("")
def status(_: AdminUser = Depends(admin_required), db: Session = Depends(get_db)):
    cfg = _cfg(db)
    return {"enabled": cfg.enabled, "client_id": cfg.client_id, "redirect_uri": cfg.redirect_uri, "connected": sp.connected()}


@admin.post("/authorize")
def authorize(_: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    cfg = _cfg(db)
    return {"url": _run(sp.authorize_url, cfg.client_id, cfg.redirect_uri)}


@admin.post("/connect")
def connect(body: CodeBody, _: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    cfg = _cfg(db)
    _run(sp.connect, cfg.client_id, cfg.redirect_uri, body.code)
    return {"connected": True}


@admin.delete("")
def disconnect(_: AdminUser = Depends(admin_session_required)):
    sp.disconnect()
    return {"connected": False}


@admin.get("/devices")
def admin_devices(_: AdminUser = Depends(admin_required), db: Session = Depends(get_db)):
    return _run(sp.devices, _ready(db))


# ------------------------------------------------------------------ frames
def _limit(device: Device) -> None:
    if not limiter.check(device.id):
        raise HTTPException(429, "Demasiadas peticiones")


class ControlBody(BaseModel):
    action: str = Field(pattern="^(play|pause|next|previous|volume|transfer)$")
    device_id: str | None = Field(None, max_length=80)
    uri: str | None = Field(None, max_length=80)
    volume: int | None = Field(None, ge=0, le=100)


@frame.get("/state")
def state(device: Device = Depends(device_required), db: Session = Depends(get_db)):
    _limit(device)
    return _run(sp.playback, _ready(db))


@frame.get("/devices")
def devices(device: Device = Depends(device_required), db: Session = Depends(get_db)):
    _limit(device)
    return _run(sp.devices, _ready(db))


@frame.get("/playlists")
def playlists(device: Device = Depends(device_required), db: Session = Depends(get_db)):
    _limit(device)
    return _run(sp.playlists, _ready(db))


@frame.get("/search")
def search(q: str = Query(min_length=1, max_length=80), device: Device = Depends(device_required),
           db: Session = Depends(get_db)):
    _limit(device)
    return _run(sp.search, _ready(db), q.strip())


@frame.post("/control")
def control(body: ControlBody, device: Device = Depends(device_required), db: Session = Depends(get_db)):
    _limit(device)
    _run(sp.control, _ready(db), body.action, body.device_id, body.uri, body.volume)
    return {"ok": True}
