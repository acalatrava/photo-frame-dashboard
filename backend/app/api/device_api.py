import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from .. import state
from ..core.config import APP_VERSION
from ..core.db import get_db, session_scope
from ..core.events import bus, sse_format
from ..models import Device, SourceStatus
from ..services import config_service
from ..services.calendar import service as cal
from ..services.cameras import service as cams
from ..services.chores import service as chores
from ..services.homeassistant import service as has
from ..services.menu import service as menu_service
from ..services.photos import service as photos
from ..services.presence import service as presence
from ..services.shopping import service as shop
from ..services.spotify import service as spotify
from ..services.updates import service as upd
from ..services.weather import service as weather
from .deps import device_required

router = APIRouter(prefix="/api/v1/device", tags=["device"])


class ShopOp(BaseModel):
    op_id: str = Field(min_length=6, max_length=64)
    type: Literal["add", "set_done", "remove", "rename"]
    id: str | None = Field(None, max_length=200)
    client_id: str | None = Field(None, max_length=64)
    name: str | None = Field(None, min_length=1, max_length=200)
    note: str = Field("", max_length=300)
    done: bool | None = None


class ShopOpsBody(BaseModel):
    ops: list[ShopOp] = Field(max_length=200)


class ChoreOp(BaseModel):
    chore_id: str = Field(max_length=32)
    person_id: str = Field("", max_length=32)
    done: bool
    day: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class ChoreOpsBody(BaseModel):
    ops: list[ChoreOp] = Field(max_length=200)


def _small(value: dict) -> dict:
    if len(json.dumps(value, default=str)) > 16 * 1024:
        raise ValueError("demasiado grande")
    return value


class HaServiceBody(BaseModel):
    entity_id: str = Field(max_length=120)
    service: str = Field(max_length=60)
    data: dict = {}

    _cap = field_validator("data")(_small)


class HeartbeatBody(BaseModel):
    app_version: str | None = Field(None, max_length=32)
    status: dict = {}

    _cap = field_validator("status")(_small)


class TelemetryBody(BaseModel):
    samples: list[list[float]] = Field(max_length=2000)


@router.get("/bootstrap")
def bootstrap(device: Device = Depends(device_required), db: Session = Depends(get_db)):
    cfg = config_service.effective_config(db, device)
    return {"server_time": time.time(), "server_version": APP_VERSION, "config": cfg,
            "recording": device.id in presence.ACTIVE}


def _shopping_cache_get(db: Session) -> dict | None:
    st = db.get(SourceStatus, "shopping:cache")
    return st.data if st and st.data else None


def _shopping_cache_put(db: Session, items: list[dict]) -> None:
    st = db.get(SourceStatus, "shopping:cache")
    if not st:
        st = SourceStatus(key="shopping:cache", data={})
        db.add(st)
    st.data = {"items": items, "at": time.time()}
    st.ok = True


async def _shopping_snapshot(db: Session) -> dict:
    provider = shop.get_provider(db, state.ha)
    try:
        items = await provider.list_items()
        _shopping_cache_put(db, items)
        return {"provider": provider.name, "ok": True, "items": items}
    except shop.ProviderError as exc:
        cached = _shopping_cache_get(db)
        return {"provider": provider.name, "ok": False, "error": str(exc),
                "items": cached["items"] if cached else [], "stale_since": cached["at"] if cached else None}


@router.get("/dashboard")
async def dashboard(device: Device = Depends(device_required), db: Session = Depends(get_db)):
    cfg = config_service.effective_config(db, device)
    dcfg = config_service.device_config(device)
    g, _ = config_service.get_global(db)
    visible = [p["id"] for p in cfg["people"]]
    ha_view = has.device_view(db, state.ha, dcfg.layout.entity_order)
    presence_entities = dcfg.presence.ha_entities
    notices = []
    for src in g.calendars:
        st = db.get(SourceStatus, f"calendar:{src.id}")
        if st and not st.ok and st.last_attempt:
            notices.append({"id": f"cal-{src.id}", "type": "calendar", "message": st.detail, "source": src.name})
    return {
        "server_time": time.time(),
        "config_version": cfg["version"],
        "events": cal.device_events(db, visible),
        "shopping": await _shopping_snapshot(db),
        "ha": ha_view,
        "chores": chores.snapshot(db, g),
        "cameras": cams.device_list(g, device),
        "menu": menu_service.for_frame(g),
        "music": {"configured": bool(g.spotify.enabled and g.spotify.client_id and spotify.connected())},
        "weather": weather.get_cached(),
        "photos": photos.device_photos(db, device, dcfg.photos.album_id) if dcfg.photos.enabled else [],
        "presence": {"ha_active": has.presence_active(db, state.ha, presence_entities)},
        "notices": notices,
    }


@router.post("/heartbeat")
def heartbeat(body: HeartbeatBody, device: Device = Depends(device_required)):
    presence.heartbeat(device, body.status, body.app_version)
    return {"server_time": time.time(), "recording": device.id in presence.ACTIVE}


@router.post("/telemetry")
def telemetry(body: TelemetryBody, device: Device = Depends(device_required), db: Session = Depends(get_db)):
    for s in body.samples:
        if len(s) < 2 or len(s) > 4:
            raise HTTPException(422, "Muestra inválida")
    return presence.ingest(db, device, body.samples)


@router.get("/shopping")
async def shopping_list(device: Device = Depends(device_required), db: Session = Depends(get_db)):
    return await _shopping_snapshot(db)


@router.post("/shopping/ops")
async def shopping_ops(body: ShopOpsBody, device: Device = Depends(device_required),
                       db: Session = Depends(get_db)):
    provider = shop.get_provider(db, state.ha)
    ops = [o.model_dump() for o in body.ops]
    for o in ops:
        if o["type"] in ("add", "rename") and not o.get("name"):
            raise HTTPException(422, "Falta el nombre")
        if o["type"] == "set_done" and o.get("done") is None:
            raise HTTPException(422, "Falta el estado")
    try:
        results = await shop.apply_ops(provider, ops, device.id)
    except shop.ProviderError as exc:
        raise HTTPException(502, str(exc)) from exc
    bus.publish("shopping.changed", {"by": device.id})
    snap = await _shopping_snapshot(db)
    return {"results": results, "shopping": snap}


@router.get("/chores")
def chores_today(device: Device = Depends(device_required), db: Session = Depends(get_db)):
    g, _ = config_service.get_global(db)
    return chores.snapshot(db, g)


@router.post("/chores/done")
def chores_done(body: ChoreOpsBody, device: Device = Depends(device_required), db: Session = Depends(get_db)):
    """Absolute states, applied in order; a replayed batch has the same result."""
    g, _ = config_service.get_global(db)
    errors = []
    chores.purge_old(db, g)
    for op in body.ops:
        try:
            chores.set_done(db, g, op.chore_id, op.person_id, op.done, device.id, op.day)
        except chores.ChoreError as exc:
            errors.append({"chore_id": op.chore_id, "error": exc.msg})
    return {"chores": chores.snapshot(db, g), "errors": errors}


@router.post("/ha/service")
async def ha_service(body: HaServiceBody, device: Device = Depends(device_required),
                     db: Session = Depends(get_db)):
    try:
        return await has.control(db, state.ha, body.entity_id, body.service, body.data)
    except has.ControlError as exc:
        raise HTTPException(exc.status, exc.msg) from exc


@router.get("/update")
def update_info(device: Device = Depends(device_required), db: Session = Depends(get_db)):
    """The published app release (if any). The frame compares versionCode itself and decides what to do."""
    g, _ = config_service.get_global(db)
    return {"mode": g.updates.mode, "package": upd.APK_PACKAGE, "release": upd.public_view(upd.published())}


@router.get("/update/apk")
def update_apk(device: Device = Depends(device_required)):
    release = upd.published()
    path = upd.apk_path(release["version_code"]) if release else None
    if not release or not path.exists():
        raise HTTPException(404, "No hay ninguna actualización publicada")
    return FileResponse(path, media_type="application/vnd.android.package-archive",
                        filename=f"homehq-{release['version_name']}.apk",
                        headers={"X-HomeHQ-Version-Code": str(release["version_code"]),
                                 "X-HomeHQ-SHA256": release["sha256"], "Cache-Control": "no-store"})


@router.get("/events")
async def events(request: Request, device: Device = Depends(device_required)):
    sub = bus.subscribe(device.id)
    version = f"{device.config_version}"

    async def gen():
        try:
            yield sse_format({"topic": "hello", "data": {"server_time": time.time(), "cfg": version}})
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(sub.queue.get(), timeout=15)
                    yield sse_format(msg)
                    if msg["topic"] == "device.revoked":
                        break
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            bus.unsubscribe(sub)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
