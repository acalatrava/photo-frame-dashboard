import secrets as pysecrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..core import security
from ..core.config import get_settings
from ..models import Device, PairingRequest
from ..services import config_service


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def create_request(db: Session, hint: dict, ip: str) -> tuple[PairingRequest, str]:
    s = get_settings()
    now = datetime.now(timezone.utc)
    # Housekeeping and a cap on parallel pending requests (anti-flood).
    for r in db.query(PairingRequest).filter(PairingRequest.status == "pending").all():
        if _aware(r.expires_at) < now:
            r.status = "expired"
    pending = db.query(PairingRequest).filter(PairingRequest.status == "pending").count()
    if pending >= 10:
        raise ValueError("demasiadas solicitudes pendientes")
    poll_secret = security.new_token(24)
    req = PairingRequest(
        id=pysecrets.token_hex(8),
        code=f"{pysecrets.randbelow(1_000_000):06d}",
        poll_hash=security.sha256_hex(poll_secret),
        hint={k: str(v)[:80] for k, v in (hint or {}).items() if k in ("name", "model", "app_version", "screen")},
        ip=ip,
        expires_at=now + timedelta(seconds=s.pairing_ttl_seconds),
    )
    db.add(req)
    db.flush()
    return req, poll_secret


def approve(db: Session, req: PairingRequest, name: str) -> Device:
    token = security.new_token(32)
    device = Device(
        id=pysecrets.token_hex(8), name=name[:80] or req.hint.get("name", "Marco"),
        token_hash=security.sha256_hex(token), media_secret=security.new_token(24),
    )
    g, _ = config_service.get_global(db)
    device.config = g.device_defaults.model_dump(mode="json")
    device.hardware = {k: v for k, v in req.hint.items() if k in ("model", "screen")}
    db.add(device)
    req.status = "approved"
    req.device_id = device.id
    # Held encrypted only until the device collects it once.
    req.token_enc = security.encrypt(token)
    db.flush()
    return device


def collect(db: Session, req: PairingRequest, poll_secret: str) -> dict:
    now = datetime.now(timezone.utc)
    if not security.constant_eq(security.sha256_hex(poll_secret), req.poll_hash):
        return {"status": "invalid"}
    if req.status == "pending" and _aware(req.expires_at) < now:
        req.status = "expired"
    if req.status == "approved":
        token = security.decrypt(req.token_enc or "")
        req.token_enc = None
        req.status = "delivered"
        db.flush()
        return {"status": "approved", "device_id": req.device_id, "device_token": token}
    return {"status": req.status}
