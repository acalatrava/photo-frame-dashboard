"""Device telemetry: heartbeats, live light-sensor ring buffer and CSV recordings for calibration."""
import csv
import secrets as pysecrets
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...models import Device, Recording

RING: dict[str, deque] = defaultdict(lambda: deque(maxlen=900))
ACTIVE: dict[str, str] = {}  # device_id -> recording id


def recording_path(rec: Recording) -> Path:
    return get_settings().recordings_dir / rec.path


def start_recording(db: Session, device: Device, name: str) -> Recording:
    stop_recording(db, device.id)
    rid = pysecrets.token_hex(6)
    rel = f"{device.id}-{rid}.csv"
    path = get_settings().recordings_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        csv.writer(fh).writerow(["t_ms", "lux", "baseline", "active"])
    rec = Recording(id=rid, device_id=device.id, name=name[:100] or "Sesión", path=rel)
    db.add(rec)
    db.flush()
    ACTIVE[device.id] = rid
    return rec


def stop_recording(db: Session, device_id: str) -> None:
    rid = ACTIVE.pop(device_id, None)
    if not rid:
        return
    rec = db.get(Recording, rid)
    if rec and not rec.ended_at:
        rec.ended_at = datetime.now(timezone.utc)
        started = rec.started_at if rec.started_at.tzinfo else rec.started_at.replace(tzinfo=timezone.utc)
        rec.duration_s = (rec.ended_at - started).total_seconds()


def ingest(db: Session, device: Device, samples: list[list[float]]) -> dict:
    """samples: [t_ms, lux, baseline, active(0/1)]. Always feeds the live ring; writes CSV if recording."""
    for s in samples:
        RING[device.id].append(s)
    rid = ACTIVE.get(device.id)
    if rid and samples:
        rec = db.get(Recording, rid)
        if rec:
            with recording_path(rec).open("a", newline="") as fh:
                csv.writer(fh).writerows(samples)
            rec.samples += len(samples)
    return {"recording": bool(rid)}


def heartbeat(device: Device, status: dict, app_version: str | None) -> None:
    device.last_status = {**status, "received_at": time.time()}
    if app_version:
        device.app_version = app_version[:32]
