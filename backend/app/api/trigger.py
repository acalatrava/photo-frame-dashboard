"""Inbound triggers: Home Assistant (or any script) asks the frames to do something right now.

Typical use is a doorbell: HA calls this endpoint and the hallway frame wakes up on the front-door camera. The call
is authenticated with an API token of scope `trigger` (or `full`), which can do nothing else.
"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.events import bus
from ..models import AdminUser, Device
from ..schemas.config import NAV_ITEMS, SOUNDS
from .deps import RateLimiter, client_ip, trigger_required

router = APIRouter(prefix="/api/v1/trigger", tags=["trigger"])
limiter = RateLimiter(120, 600)

VIEWS = ["home", "settings"] + NAV_ITEMS


class TriggerBody(BaseModel):
    action: Literal["show_view", "alert", "wake", "sleep"]
    # A frame id or name. Empty means every frame.
    device: str | None = Field(None, max_length=80)
    view: str | None = None
    # With show_view on "cameras": open this camera full screen.
    camera: str | None = Field(None, max_length=40)
    message: str = Field("", max_length=200)
    speak: bool = False
    sound: Literal["chime", "bell", "soft", "beep", "melody", "none"] = "bell"
    volume: int = Field(80, ge=1, le=100)
    # How long the screen or the alert stays before the frame goes back to what it was doing. 0 keeps it.
    duration_s: int = Field(30, ge=0, le=900)

    @model_validator(mode="after")
    def _check(self):
        if self.action == "show_view" and self.view not in VIEWS:
            raise ValueError("view debe ser una de: " + ", ".join(VIEWS))
        if self.action == "alert" and self.sound == "none" and not self.message.strip():
            raise ValueError("una alerta necesita un mensaje o un sonido")
        return self


def _targets(db: Session, wanted: str | None) -> list[Device]:
    devices = db.query(Device).filter(Device.status == "active").all()
    if not wanted:
        return devices
    key = wanted.strip().lower()
    found = [d for d in devices if d.id.lower() == key or d.name.strip().lower() == key]
    if not found:
        raise HTTPException(404, f"No hay ningún marco llamado «{wanted}»")
    return found


def publish_trigger(db: Session, body: TriggerBody) -> dict:
    targets = _targets(db, body.device)
    payload = body.model_dump(exclude={"device"}, exclude_none=True)
    payload["type"] = "trigger"
    online = bus.connected_devices()
    for d in targets:
        bus.publish("device.command", payload, d.id)
    return {"sent": [d.id for d in targets if d.id in online],
            "offline": [d.id for d in targets if d.id not in online]}


@router.post("")
def fire(body: TriggerBody, request: Request, _: AdminUser = Depends(trigger_required), db: Session = Depends(get_db)):
    if not limiter.check(client_ip(request)):
        raise HTTPException(429, "Demasiados disparadores seguidos")
    return publish_trigger(db, body)
