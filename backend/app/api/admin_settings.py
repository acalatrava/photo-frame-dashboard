import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import state
from ..core import secrets_store
from ..core.config import APP_VERSION, get_settings
from ..core.db import get_db
from ..core.events import bus
from ..models import Album, Device, Photo, Recording, SourceStatus
from ..schemas.config import GlobalConfig
from ..services import config_service
from ..services.calendar import service as cal
from ..services.cameras import service as cams
from ..services.homeassistant import service as has
from ..services.homeassistant.client import HAError
from ..services.photos import service as photos
from ..services.presence import service as presence
from ..services.weather import service as weather
from .deps import admin_required

router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(admin_required)])


# ------------------------------------------------------------------ global config
@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    g, version = config_service.get_global(db)
    return {
        "config": g.model_dump(mode="json"), "version": version,
        "secrets": {
            "homeassistant_token": secrets_store.has_secret(db, has.SECRET),
            "calendars": {c.id: secrets_store.has_secret(db, cal.secret_name(c.id)) for c in g.calendars},
        },
    }


@router.put("/config")
def put_config(body: dict, db: Session = Depends(get_db)):
    try:
        cfg = GlobalConfig.model_validate(body)
    except Exception as exc:  # pydantic ValidationError -> 422 with readable detail
        raise HTTPException(422, _errors(exc)) from exc
    old, _ = config_service.get_global(db)
    version = config_service.save_global(db, cfg)
    for c in old.calendars:
        if c.id not in {n.id for n in cfg.calendars}:
            secrets_store.delete_secret(db, cal.secret_name(c.id))
    state.ha.reload()
    return {"version": version}


def _errors(exc: Exception) -> str:
    errs = getattr(exc, "errors", None)
    if not errs:
        return str(exc)
    return "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in errs())


# ------------------------------------------------------------------ Home Assistant
class TokenBody(BaseModel):
    token: str = Field(min_length=10, max_length=2000)


class HaTestBody(BaseModel):
    url: str | None = None
    token: str | None = None
    verify_tls: bool | None = None


@router.put("/homeassistant/token")
def set_ha_token(body: TokenBody, db: Session = Depends(get_db)):
    secrets_store.set_secret(db, has.SECRET, body.token.strip())
    db.commit()
    state.ha.reload()
    return {"ok": True}


@router.delete("/homeassistant/token")
def delete_ha_token(db: Session = Depends(get_db)):
    secrets_store.delete_secret(db, has.SECRET)
    db.commit()
    state.ha.reload()
    return {"ok": True}


@router.post("/homeassistant/test")
async def test_ha(body: HaTestBody, db: Session = Depends(get_db)):
    g, _ = config_service.get_global(db)
    url = (body.url or g.homeassistant.url).rstrip("/")
    token = body.token or secrets_store.get_secret(db, has.SECRET)
    if not url or not token:
        raise HTTPException(400, "Falta la URL o el token de Home Assistant")
    verify = g.homeassistant.verify_tls if body.verify_tls is None else body.verify_tls
    try:
        return {"ok": True, **await state.ha.check({"url": url, "token": token, "verify_tls": verify})}
    except HAError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/homeassistant/entities")
def ha_entities(domain: str = "", db: Session = Depends(get_db)):
    if not state.ha.connected:
        raise HTTPException(503, "Home Assistant no está conectado")
    out = []
    for eid, s in sorted(state.ha.entities.items()):
        d = eid.split(".")[0]
        if domain and d != domain:
            continue
        if d not in ("light", "switch", "climate", "cover", "camera", "sensor", "binary_sensor", "scene", "script",
                     "todo", "person"):
            continue
        a = s["attributes"]
        out.append({"entity_id": eid, "domain": d, "name": a.get("friendly_name", eid), "state": s["state"],
                    "device_class": a.get("device_class"), "unit": a.get("unit_of_measurement"),
                    "controllable": d in has.CONTROLLABLE_DOMAINS})
    return out


# ------------------------------------------------------------------ calendars
class PasswordBody(BaseModel):
    password: str = Field(min_length=1, max_length=500)


@router.put("/calendars/{source_id}/password")
def set_calendar_password(source_id: str, body: PasswordBody, db: Session = Depends(get_db)):
    g, _ = config_service.get_global(db)
    if source_id not in {c.id for c in g.calendars}:
        raise HTTPException(404, "Calendario desconocido")
    secrets_store.set_secret(db, cal.secret_name(source_id), body.password)
    return {"ok": True}


@router.post("/calendars/{source_id}/sync")
async def sync_calendar(source_id: str):
    res = await cal.run_sync(source_id)
    if not res["ok"]:
        raise HTTPException(502, res["detail"])
    return res


# ------------------------------------------------------------------ albums & photos
class AlbumBody(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class PhotoPatch(BaseModel):
    caption: str = Field("", max_length=200)


def _album_dict(db: Session, a: Album) -> dict:
    n = db.query(Photo).filter(Photo.album_id == a.id).count()
    return {"id": a.id, "name": a.name, "photos": n}


@router.get("/albums")
def list_albums(db: Session = Depends(get_db)):
    return [_album_dict(db, a) for a in db.query(Album).order_by(Album.name)]


@router.post("/albums")
def create_album(body: AlbumBody, db: Session = Depends(get_db)):
    try:
        a = photos.create_album(db, body.name)
    except photos.PhotoError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _album_dict(db, a)


@router.put("/albums/{album_id}")
def rename_album(album_id: str, body: AlbumBody, db: Session = Depends(get_db)):
    a = db.get(Album, album_id)
    if not a:
        raise HTTPException(404, "Álbum no encontrado")
    if db.query(Album).filter(Album.name == body.name, Album.id != a.id).first():
        raise HTTPException(400, "Ya existe un álbum con ese nombre")
    a.name = body.name.strip()
    return _album_dict(db, a)


@router.delete("/albums/{album_id}")
def remove_album(album_id: str, db: Session = Depends(get_db)):
    a = db.get(Album, album_id)
    if not a:
        raise HTTPException(404, "Álbum no encontrado")
    photos.delete_album(db, a)
    return {"ok": True}


@router.get("/albums/{album_id}/photos")
def album_photos(album_id: str, db: Session = Depends(get_db)):
    if not db.get(Album, album_id):
        raise HTTPException(404, "Álbum no encontrado")
    rows = db.query(Photo).filter(Photo.album_id == album_id).order_by(Photo.position).all()
    return [photos.photo_dict(p) | {"size_bytes": p.size_bytes} for p in rows]


@router.post("/albums/{album_id}/photos")
async def upload_photo(album_id: str, request: Request, filename: str = "foto.jpg",
                       db: Session = Depends(get_db)):
    """Raw body upload (one file per request) so no multipart dependency is needed."""
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(404, "Álbum no encontrado")
    limit = get_settings().photo_max_upload_mb * 1024 * 1024
    declared = int(request.headers.get("content-length") or 0)
    if declared > limit:
        raise HTTPException(413, f"La foto supera {get_settings().photo_max_upload_mb} MB")
    chunks, total = [], 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            raise HTTPException(413, f"La foto supera {get_settings().photo_max_upload_mb} MB")
        chunks.append(chunk)
    try:
        photo, created = await asyncio.to_thread(photos.add_photo, db, album, b"".join(chunks), filename)
    except photos.PhotoError as exc:
        raise HTTPException(400, str(exc)) from exc
    if created:
        bus.publish("photos.updated", {"album": album_id})
    return {**photos.photo_dict(photo), "created": created}


@router.patch("/photos/{photo_id}")
def patch_photo(photo_id: str, body: PhotoPatch, db: Session = Depends(get_db)):
    p = db.get(Photo, photo_id)
    if not p:
        raise HTTPException(404, "Foto no encontrada")
    p.caption = body.caption.strip()
    bus.publish("photos.updated", {"album": p.album_id})
    return photos.photo_dict(p)


@router.delete("/photos/{photo_id}")
def remove_photo(photo_id: str, db: Session = Depends(get_db)):
    p = db.get(Photo, photo_id)
    if not p:
        raise HTTPException(404, "Foto no encontrada")
    album = p.album_id
    photos.delete_photo(db, p)
    bus.publish("photos.updated", {"album": album})
    return {"ok": True}


# ------------------------------------------------------------------ telemetry / recordings
class RecordingBody(BaseModel):
    action: str = Field(pattern="^(start|stop)$")
    name: str = Field("", max_length=100)


@router.post("/devices/{device_id}/recording")
def recording(device_id: str, body: RecordingBody, db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d or d.status != "active":
        raise HTTPException(404, "Dispositivo no encontrado")
    if body.action == "start":
        rec = presence.start_recording(db, d, body.name)
        bus.publish("recording.changed", {"recording": True}, d.id)
        return {"recording": True, "id": rec.id}
    presence.stop_recording(db, d.id)
    bus.publish("recording.changed", {"recording": False}, d.id)
    return {"recording": False}


@router.get("/devices/{device_id}/telemetry")
def device_telemetry(device_id: str, db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d:
        raise HTTPException(404, "Dispositivo no encontrado")
    return {"status": d.last_status, "samples": list(presence.RING.get(d.id, []))[-600:],
            "recording": d.id in presence.ACTIVE}


@router.get("/recordings")
def list_recordings(db: Session = Depends(get_db)):
    rows = db.query(Recording).order_by(Recording.started_at.desc()).limit(50).all()
    return [{"id": r.id, "device_id": r.device_id, "name": r.name, "samples": r.samples,
             "started_at": r.started_at.isoformat(), "duration_s": r.duration_s,
             "active": r.id in presence.ACTIVE.values()} for r in rows]


@router.get("/recordings/{rec_id}/csv")
def download_recording(rec_id: str, db: Session = Depends(get_db)):
    r = db.get(Recording, rec_id)
    if not r or not presence.recording_path(r).exists():
        raise HTTPException(404, "Grabación no encontrada")
    return FileResponse(presence.recording_path(r), media_type="text/csv", filename=f"lux-{r.id}.csv")


# ------------------------------------------------------------------ status
@router.get("/status")
def status(db: Session = Depends(get_db)):
    g, _ = config_service.get_global(db)
    cals = []
    for c in g.calendars:
        st = db.get(SourceStatus, f"calendar:{c.id}")
        cals.append({"id": c.id, "name": c.name, "ok": st.ok if st else None, "detail": st.detail if st else "",
                     "last_success": st.last_success.isoformat() if st and st.last_success else None})
    w = db.get(SourceStatus, weather.KEY)
    return {
        "version": APP_VERSION,
        "homeassistant": {"enabled": g.homeassistant.enabled, "connected": state.ha.connected,
                          "version": state.ha.version, "error": state.ha.last_error,
                          "entities": len(state.ha.entities)},
        "calendars": cals,
        "weather": {"configured": bool(g.general.location), "ok": w.ok if w else None},
        "devices": db.query(Device).filter(Device.status == "active").count(),
        "https": None,
    }


# ------------------------------------------------------------------ cameras
@router.get("/frigate/cameras")
async def frigate_cameras(db: Session = Depends(get_db)):
    g, _ = config_service.get_global(db)
    try:
        return await cams.frigate_cameras(g)
    except cams.CameraError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/cameras/{camera_id}/snapshot")
async def camera_snapshot(camera_id: str, db: Session = Depends(get_db)):
    g, _ = config_service.get_global(db)
    cam = next((c for c in g.cameras if c.id == camera_id), None)
    if not cam:
        raise HTTPException(404, "Cámara no encontrada")
    try:
        data = await cams.fetch_snapshot(g, cam, state.ha)
    except cams.CameraError as exc:
        raise HTTPException(502, str(exc)) from exc
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": "no-store"})
