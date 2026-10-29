from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core import security
from ..core.db import get_db
from ..core.events import bus
from ..devices import service
from ..models import AdminUser, Device, PairingRequest
from ..schemas.config import DeviceConfig
from ..services import config_service
from .deps import admin_required
from .trigger import TriggerBody, publish_trigger

router = APIRouter(prefix="/api/v1/admin", tags=["admin-devices"])


class ApproveBody(BaseModel):
    code: str = Field(min_length=6, max_length=6)
    name: str = Field(min_length=1, max_length=80)


class DevicePatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    config: dict | None = None


class CommandBody(BaseModel):
    type: str = Field(pattern="^(reload|wake|sleep|identify|update)$")


def device_dict(d: Device) -> dict:
    online = d.id in bus.connected_devices()
    return {
        "id": d.id, "name": d.name, "status": d.status, "online": online,
        "app_version": d.app_version, "last_ip": d.last_ip, "hardware": d.hardware,
        "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
        "last_status": d.last_status, "config_version": d.config_version,
        "created_at": d.created_at.isoformat(),
    }


@router.get("/pairing")
def list_pairing(_: AdminUser = Depends(admin_required), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    out = []
    for r in db.query(PairingRequest).filter(PairingRequest.status == "pending").all():
        exp = r.expires_at if r.expires_at.tzinfo else r.expires_at.replace(tzinfo=timezone.utc)
        if exp < now:
            r.status = "expired"
            continue
        out.append({"id": r.id, "hint": r.hint, "ip": r.ip, "created_at": r.created_at.isoformat(),
                    "expires_at": exp.isoformat()})
    return out


@router.post("/pairing/{request_id}/approve")
def approve(request_id: str, body: ApproveBody, _: AdminUser = Depends(admin_required),
            db: Session = Depends(get_db)):
    req = db.get(PairingRequest, request_id)
    if not req or req.status != "pending":
        raise HTTPException(404, "Solicitud no encontrada o caducada")
    # The admin must type the code shown on the frame: proves the physical device is the one approved.
    if not security.constant_eq(body.code, req.code):
        raise HTTPException(400, "El código no coincide con el que muestra el marco")
    device = service.approve(db, req, body.name)
    return device_dict(device)


@router.post("/pairing/{request_id}/reject")
def reject(request_id: str, _: AdminUser = Depends(admin_required), db: Session = Depends(get_db)):
    req = db.get(PairingRequest, request_id)
    if req and req.status == "pending":
        req.status = "rejected"
    return {"ok": True}


@router.get("/devices")
def list_devices(_: AdminUser = Depends(admin_required), db: Session = Depends(get_db)):
    return [device_dict(d) for d in db.query(Device).filter(Device.status == "active").order_by(Device.created_at)]


@router.get("/devices/{device_id}")
def get_device(device_id: str, _: AdminUser = Depends(admin_required), db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d:
        raise HTTPException(404, "Dispositivo no encontrado")
    return {**device_dict(d), "config": config_service.device_config(d).model_dump(mode="json")}


@router.put("/devices/{device_id}")
def update_device(device_id: str, body: DevicePatch, _: AdminUser = Depends(admin_required),
                  db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d:
        raise HTTPException(404, "Dispositivo no encontrado")
    if body.name:
        d.name = body.name
    if body.config is not None:
        cfg = DeviceConfig.model_validate(body.config)
        config_service.set_device_config(db, d, cfg)
    elif body.name:
        d.config_version += 1
        bus.publish("config.changed", {"scope": "device", "version": d.config_version}, d.id)
    return {**device_dict(d), "config": config_service.device_config(d).model_dump(mode="json")}


@router.delete("/devices/{device_id}")
def revoke_device(device_id: str, _: AdminUser = Depends(admin_required), db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d:
        raise HTTPException(404, "Dispositivo no encontrado")
    d.status = "revoked"
    bus.publish("device.revoked", {}, d.id)
    return {"ok": True}


@router.post("/devices/{device_id}/command")
def send_command(device_id: str, body: CommandBody, _: AdminUser = Depends(admin_required),
                 db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d or d.status != "active":
        raise HTTPException(404, "Dispositivo no encontrado")
    bus.publish("device.command", {"type": body.type}, d.id)
    return {"ok": True, "delivered_to_online": d.id in bus.connected_devices()}


@router.post("/devices/{device_id}/trigger")
def trigger_device(device_id: str, body: TriggerBody, _: AdminUser = Depends(admin_required),
                   db: Session = Depends(get_db)):
    """Lets the panel try an alert or a screen on one frame, the same way Home Assistant would."""
    d = db.get(Device, device_id)
    if not d or d.status != "active":
        raise HTTPException(404, "Dispositivo no encontrado")
    return publish_trigger(db, body.model_copy(update={"device": d.id}))
