import time

from sqlalchemy.orm import Session

from ...core import secrets_store
from ...core.db import session_scope
from ...schemas.config import ENTITY_ID
from .. import config_service
from .client import HAClient, HAError

SECRET = "homeassistant.token"

# domain -> service -> allowed data keys. Anything else is rejected.
ALLOWED_SERVICES: dict[str, dict[str, set[str]]] = {
    "light": {"turn_on": {"brightness_pct"}, "turn_off": set(), "toggle": set()},
    "switch": {"turn_on": set(), "turn_off": set(), "toggle": set()},
    "scene": {"turn_on": set()},
    "script": {"turn_on": set()},
    "climate": {"set_temperature": {"temperature"}, "set_hvac_mode": {"hvac_mode"}},
    "cover": {"open_cover": set(), "close_cover": set(), "stop_cover": set(), "toggle": set(),
              "set_cover_position": {"position"}},
}

CONTROLLABLE_DOMAINS = tuple(ALLOWED_SERVICES)


class ControlError(Exception):
    def __init__(self, status: int, msg: str):
        super().__init__(msg)
        self.status, self.msg = status, msg


def load_runtime_config() -> dict | None:
    """Config dict for the client, or None when HA is not configured. Runs in the loop thread."""
    with session_scope() as db:
        g, _ = config_service.get_global(db)
        token = secrets_store.get_secret(db, SECRET)
        if not g.homeassistant.enabled or not g.homeassistant.url or not token:
            return None
        return {"url": g.homeassistant.url, "token": token, "verify_tls": g.homeassistant.verify_tls}


def readable_entities(db: Session) -> list[str]:
    """Entities frames may read: authorised + presence sensors + people + the shopping list."""
    g, _ = config_service.get_global(db)
    ids = list(g.homeassistant.authorized_entities)
    ids += [p.ha_person for p in g.people if p.ha_person]
    if g.shopping.ha_entity:
        ids.append(g.shopping.ha_entity)
    for dev_cfg in _all_device_presence(db):
        ids += dev_cfg
    return list(dict.fromkeys(ids))


def _all_device_presence(db: Session):
    from ...models import Device
    for d in db.query(Device).filter(Device.status == "active"):
        yield (d.config or {}).get("presence", {}).get("ha_entities", []) or []


def device_view(db: Session, ha: HAClient, order: list[str]) -> dict:
    g, _ = config_service.get_global(db)
    wanted = list(dict.fromkeys(order + g.homeassistant.authorized_entities))
    authorized = set(g.homeassistant.authorized_entities)
    entities = []
    for eid in wanted:
        if eid not in authorized:
            continue
        s = ha.entities.get(eid)
        if s:
            entities.append({**s, "controllable": eid.split(".")[0] in CONTROLLABLE_DOMAINS})
    people = {}
    for p in g.people:
        if p.ha_person and p.ha_person in ha.entities:
            people[p.id] = ha.entities[p.ha_person]["state"]
    return {
        "enabled": g.homeassistant.enabled,
        "connected": ha.connected,
        "last_event_age_s": round(time.time() - ha.last_event_ts) if ha.last_event_ts else None,
        "entities": entities,
        "people": people,
        "meta": {k: v.model_dump(exclude_defaults=True) for k, v in g.homeassistant.entity_meta.items()
                 if k in authorized},
    }


def presence_active(db: Session, ha: HAClient, entity_ids: list[str]) -> bool | None:
    """True/False from real HA sensors, None when HA data is unavailable."""
    if not ha.connected or not entity_ids:
        return None
    return any(ha.entities.get(e, {}).get("state") == "on" for e in entity_ids)


async def control(db: Session, ha: HAClient, entity_id: str, service: str, data: dict) -> dict:
    if not ENTITY_ID.match(entity_id):
        raise ControlError(422, "entity_id inválido")
    g, _ = config_service.get_global(db)
    if not g.homeassistant.enabled:
        raise ControlError(409, "Home Assistant no está activado")
    if entity_id not in g.homeassistant.authorized_entities:
        raise ControlError(403, "Entidad no autorizada")
    if not ha.connected:
        raise ControlError(503, "Home Assistant no está conectado")
    domain = entity_id.split(".")[0]
    allowed = ALLOWED_SERVICES.get(domain, {}).get(service)
    if allowed is None:
        raise ControlError(403, "Servicio no permitido")
    extra = set(data) - allowed
    if extra:
        raise ControlError(422, f"Parámetros no permitidos: {', '.join(sorted(extra))}")
    payload = {"entity_id": entity_id, **data}
    if "brightness_pct" in data and not (1 <= int(data["brightness_pct"]) <= 100):
        raise ControlError(422, "brightness_pct fuera de rango")
    if "temperature" in data:
        try:
            t = float(data["temperature"])
        except (TypeError, ValueError) as exc:
            raise ControlError(422, "temperature inválida") from exc
        if not 5 <= t <= 35:
            raise ControlError(422, "temperature fuera de rango")
        payload["temperature"] = t
    if "position" in data:
        try:
            pos = int(data["position"])
        except (TypeError, ValueError) as exc:
            raise ControlError(422, "position inválida") from exc
        if not 0 <= pos <= 100:
            raise ControlError(422, "position fuera de rango")
        payload["position"] = pos
    if "hvac_mode" in data and not isinstance(data["hvac_mode"], str):
        raise ControlError(422, "hvac_mode inválido")
    try:
        await ha.call_service(domain, service, payload)
    except HAError as exc:
        raise ControlError(502, str(exc)) from exc
    return {"ok": True}
