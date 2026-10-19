from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.orm import Session

from ..core import security
from .. import state
from ..core.db import get_db, session_scope
from ..models import Device, Photo
from ..services import config_service
from ..services.cameras import service as cams
from ..services.photos import service as photos
from .deps import admin_required

router = APIRouter(tags=["media"])
HEADERS = {"Cache-Control": "private, max-age=31536000, immutable"}


@router.get("/media/p/{device_id}/{photo_id}/{size}")
def device_media(device_id: str, photo_id: str, size: str, s: str = Query(max_length=64),
                 db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    path = f"/media/p/{device_id}/{photo_id}/{size}"
    if not device or device.status != "active" or \
            not security.constant_eq(s, security.media_signature(device.media_secret, path)):
        raise HTTPException(403, "Acceso denegado")
    photo = db.get(Photo, photo_id)
    if not photo or size not in photos.SIZES or size == "master":
        raise HTTPException(404, "No encontrada")
    f = photos.file_path(photo.album_id, photo.id, size)
    if not f.exists():
        raise HTTPException(404, "No encontrada")
    return FileResponse(f, media_type="image/jpeg", headers=HEADERS)


@router.get("/api/v1/admin/photos/{photo_id}/{size}")
def admin_media(photo_id: str, size: str, _=Depends(admin_required), db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo or size not in photos.SIZES:
        raise HTTPException(404, "No encontrada")
    f = photos.file_path(photo.album_id, photo.id, size)
    if not f.exists():
        raise HTTPException(404, "No encontrada")
    return FileResponse(f, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})


@router.get("/media/cam/{device_id}/{camera_id}/{kind}")
async def camera_media(device_id: str, camera_id: str, kind: str, request: Request, s: str = Query(max_length=64)):
    if kind not in ("snapshot", "stream"):
        raise HTTPException(404, "No encontrada")
    with session_scope() as db:
        device = db.get(Device, device_id)
        if not device or device.status != "active" or not cams.verify_sig(device, camera_id, kind, s):
            raise HTTPException(403, "Acceso denegado")
        g, _ = config_service.get_global(db)
    cam = cams.find(g, camera_id)
    if not cam:
        raise HTTPException(404, "Cámara no encontrada")
    try:
        frame = await cams.fetch_snapshot(g, cam, state.ha)
    except cams.CameraError as exc:
        raise HTTPException(502, str(exc)) from exc
    headers = {"Cache-Control": "no-store"}
    if kind == "snapshot":
        return Response(frame, media_type="image/jpeg", headers=headers)
    return StreamingResponse(cams.mjpeg(g, cam, state.ha, request.is_disconnected, first=frame),
                             media_type=f"multipart/x-mixed-replace; boundary={cams.BOUNDARY}", headers=headers)
