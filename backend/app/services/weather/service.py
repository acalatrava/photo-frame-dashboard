"""Weather from Open-Meteo (no API key). Cached in the database; stale data is served on failure."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from ...core.db import session_scope
from ...core.events import bus
from ...models import SourceStatus
from .. import config_service

log = logging.getLogger("homehq.weather")
URL = "https://api.open-meteo.com/v1/forecast"
KEY = "weather"


def icon_for(code: int, is_day: int) -> str:
    if code == 0:
        return "sun" if is_day else "moon"
    if code in (1, 2):
        return "partly" if is_day else "moon"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99):
        return "rain"
    return "cloud"


def transform(raw: dict) -> dict:
    h = raw["hourly"]
    d = raw["daily"]
    cur = raw.get("current", {})
    return {
        "date": d["time"][0],
        "hi": round(d["temperature_2m_max"][0]), "lo": round(d["temperature_2m_min"][0]),
        "t": [round(x) if x is not None else None for x in h["temperature_2m"]],
        "c": [icon_for(int(c or 0), int(day)) for c, day in zip(h["weather_code"], h["is_day"])],
        "p": [int(x or 0) for x in h["precipitation_probability"]],
        "feels": round(cur["apparent_temperature"]) if cur.get("apparent_temperature") is not None else None,
        "humidity": cur.get("relative_humidity_2m"),
        "wind": round(cur["wind_speed_10m"]) if cur.get("wind_speed_10m") is not None else None,
    }


async def refresh() -> bool:
    with session_scope() as db:
        g, _ = config_service.get_global(db)
        loc, tz = g.general.location, g.general.timezone
    if not loc:
        return False
    params = {
        "latitude": loc.latitude, "longitude": loc.longitude, "timezone": tz, "forecast_days": 2,
        "hourly": "temperature_2m,precipitation_probability,weather_code,is_day",
        "daily": "temperature_2m_max,temperature_2m_min",
        "current": "apparent_temperature,relative_humidity_2m,wind_speed_10m",
    }
    now = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(URL, params=params)
        r.raise_for_status()
        data = transform(r.json())
        ok, detail = True, "ok"
    except Exception as exc:  # noqa: BLE001
        data, ok, detail = None, False, f"{exc.__class__.__name__}"
        log.warning("weather refresh failed: %s", detail)
    with session_scope() as db:
        st = db.get(SourceStatus, KEY)
        if not st:
            st = SourceStatus(key=KEY, data={})
            db.add(st)
        st.last_attempt, st.ok, st.detail = now, ok, detail
        if ok:
            st.last_success = now
            st.data = data
    if ok:
        bus.publish("weather.updated", {})
    return ok


def get_cached() -> dict | None:
    with session_scope() as db:
        st = db.get(SourceStatus, KEY)
        if not st or not st.data:
            return None
        return {**st.data, "stale": not st.ok,
                "fetched_at": st.last_success.isoformat() if st.last_success else None}


async def scheduler_loop() -> None:
    while True:
        try:
            await refresh()
        except Exception:  # noqa: BLE001
            log.exception("weather scheduler error")
        await asyncio.sleep(1800)
