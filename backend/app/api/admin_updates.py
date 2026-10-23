import asyncio
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.db import get_db
from ..core.events import bus
from ..models import AdminUser
from ..schemas.config import UpdatesConfig
from ..services import config_service
from ..services.updates import service as upd
from .deps import admin_required, admin_session_required

router = APIRouter(prefix="/api/v1/admin/updates", tags=["admin-updates"])

# What the frames install is code that runs on them, so changing it needs a logged-in admin session; an API token
# (even a full one) can only read this section and change the update mode.


class UpdateSettings(BaseModel):
    mode: Literal["off", "notify", "auto"]


def _overview(db: Session) -> dict:
    g, _ = config_service.get_global(db)
    code = upd.published_code()
    return {"mode": g.updates.mode, "published": code,
            "releases": [upd.public_view(m) | {"filename": m["filename"]} for m in upd.list_releases()]}


@router.get("")
def overview(_: AdminUser = Depends(admin_required), db: Session = Depends(get_db)):
    return _overview(db)


@router.post("")
async def upload(request: Request, filename: str = "homehq.apk", notes: str = "",
                 _: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    """Raw body upload, like photos. The APK is stored but not offered to the frames until it is published."""
    limit = get_settings().apk_max_upload_mb * 1024 * 1024
    if int(request.headers.get("content-length") or 0) > limit:
        raise HTTPException(413, f"El APK supera {get_settings().apk_max_upload_mb} MB")
    chunks, total = [], 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            raise HTTPException(413, f"El APK supera {get_settings().apk_max_upload_mb} MB")
        chunks.append(chunk)
    try:
        release, created = await asyncio.to_thread(upd.add_release, b"".join(chunks), filename, notes)
    except upd.UpdateError as exc:
        raise HTTPException(exc.status, exc.msg) from exc
    return {"release": upd.public_view(release), "created": created}


@router.post("/{version_code}/publish")
def publish(version_code: int, _: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    try:
        release = upd.publish(version_code)
    except upd.UpdateError as exc:
        raise HTTPException(exc.status, exc.msg) from exc
    bus.publish("update.changed", {"version_code": release["version_code"]})
    return _overview(db)


@router.post("/unpublish")
def unpublish(_: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    upd.unpublish()
    bus.publish("update.changed", {"version_code": None})
    return _overview(db)


@router.delete("/{version_code}")
def remove(version_code: int, _: AdminUser = Depends(admin_session_required), db: Session = Depends(get_db)):
    try:
        upd.delete(version_code)
    except upd.UpdateError as exc:
        raise HTTPException(exc.status, exc.msg) from exc
    return _overview(db)


@router.put("/settings")
def settings(body: UpdateSettings, _: AdminUser = Depends(admin_required), db: Session = Depends(get_db)):
    g, _v = config_service.get_global(db)
    g.updates = UpdatesConfig(mode=body.mode)
    config_service.save_global(db, g)
    return _overview(db)
