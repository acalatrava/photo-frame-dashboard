from sqlalchemy.orm import Session

from ..core.events import bus
from ..models import ConfigDoc, Device
from ..schemas.config import DeviceConfig, GlobalConfig, migrate_device, migrate_global, normalize_nav

KEY = "global"


def get_global(db: Session) -> tuple[GlobalConfig, int]:
    row = db.get(ConfigDoc, KEY)
    if not row:
        row = ConfigDoc(key=KEY, value=GlobalConfig().model_dump(mode="json"), version=1)
        db.add(row)
        db.flush()
    return GlobalConfig.model_validate(migrate_global(row.value)), row.version


def save_global(db: Session, cfg: GlobalConfig) -> int:
    row = db.get(ConfigDoc, KEY)
    data = cfg.model_dump(mode="json")
    if row:
        row.value = data
        row.version += 1
    else:
        row = ConfigDoc(key=KEY, value=data, version=1)
        db.add(row)
    db.flush()
    bus.publish("config.changed", {"scope": "global", "version": row.version})
    return row.version


def device_config(device: Device) -> DeviceConfig:
    return DeviceConfig.model_validate(migrate_device(device.config or {}))


def effective_config(db: Session, device: Device) -> dict:
    """Everything a frame needs to run. Never includes secrets or integration credentials."""
    g, gver = get_global(db)
    d = device_config(device)
    language = g.general.language if d.language == "inherit" else d.language
    visible = d.layout.person_ids or [p.id for p in g.people]
    return {
        "device": {"id": device.id, "name": device.name},
        "version": f"{gver}.{device.config_version}",
        "general": {
            "language": language,
            "timezone": g.general.timezone,
            "location": g.general.location.model_dump() if g.general.location else None,
            "nav_order": normalize_nav(g.general.nav_order),
        },
        "people": [p.model_dump(exclude={"ha_person"}) | {"has_presence": bool(p.ha_person)}
                   for p in g.people if p.id in visible],
        "shopping": {"provider": g.shopping.provider},
        "homeassistant": {"enabled": g.homeassistant.enabled},
        "device_config": d.model_dump(mode="json"),
    }


def set_device_config(db: Session, device: Device, cfg: DeviceConfig) -> None:
    device.config = cfg.model_dump(mode="json")
    device.config_version += 1
    db.flush()
    bus.publish("config.changed", {"scope": "device", "version": device.config_version}, device.id)
