"""Calendar sync: iCalendar subscriptions (ICS/webcal) and CalDAV (iCloud, Nextcloud, ...).

Occurrences are expanded server-side for a rolling window and cached in SQLite, so the frames
keep showing the last known agenda when the calendar provider (or the Internet) is down.
"""
import asyncio
import hashlib
import logging
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
import icalendar
import recurring_ical_events
from sqlalchemy.orm import Session

from ...core import secrets_store
from ...core.db import session_scope
from ...core.events import bus
from ...models import CalendarEvent, SourceStatus
from ...schemas.config import CalendarSource
from .. import config_service
from .legacy_emoji import LEGACY_EMOJI

log = logging.getLogger("homehq.calendar")
PAST_DAYS, FUTURE_DAYS = 45, 150


def secret_name(source_id: str) -> str:
    return f"calendar.{source_id}.password"


def _to_local(value, tz: ZoneInfo):
    """-> (iso string, all_day)."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=tz)
        return value.astimezone(tz).isoformat(timespec="seconds"), False
    if isinstance(value, date):
        return value.isoformat(), True
    raise ValueError("fecha no válida")


def _occurrences(cal: icalendar.Calendar, start: datetime, end: datetime, tz: ZoneInfo) -> list[dict]:
    out = []
    for ev in recurring_ical_events.of(cal).between(start, end):
        try:
            dtstart = ev.get("DTSTART").dt
            dtend_prop = ev.get("DTEND")
            if dtend_prop is not None:
                dtend = dtend_prop.dt
            elif ev.get("DURATION") is not None:
                dtend = dtstart + ev.get("DURATION").dt
            else:
                dtend = dtstart + (timedelta(days=1) if not isinstance(dtstart, datetime) else timedelta(0))
            s, all_day = _to_local(dtstart, tz)
            e, _ = _to_local(dtend, tz)
        except Exception:  # noqa: BLE001 - skip malformed occurrences, keep the rest
            continue
        out.append({
            "uid": str(ev.get("UID", "")), "title": str(ev.get("SUMMARY", "")).strip() or "(sin título)",
            "start": s, "end": e, "all_day": all_day, "location": str(ev.get("LOCATION", "") or ""),
            "notes": str(ev.get("DESCRIPTION", "") or "")[:1000],
        })
    return out


def parse_ics(data: bytes, tz: ZoneInfo, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(tz)
    cal = icalendar.Calendar.from_ical(data)
    return _occurrences(cal, now - timedelta(days=PAST_DAYS), now + timedelta(days=FUTURE_DAYS), tz)


async def fetch_ics(src: CalendarSource, tz: ZoneInfo) -> list[dict]:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        r = await c.get(src.url)
    r.raise_for_status()
    return await asyncio.to_thread(parse_ics, r.content, tz)


def _caldav_fetch(src: CalendarSource, password: str, tz: ZoneInfo) -> list[dict]:
    import caldav

    now = datetime.now(tz)
    start, end = now - timedelta(days=PAST_DAYS), now + timedelta(days=FUTURE_DAYS)
    out: list[dict] = []
    with caldav.DAVClient(url=src.url, username=src.username, password=password, timeout=30) as client:
        principal = client.principal()
        for cal in principal.calendars():
            name = str(cal.get_display_name() or "")
            if src.calendar_name and name != src.calendar_name:
                continue
            for ev in cal.search(start=start, end=end, event=True, expand=True):
                ical = ev.icalendar_instance
                wrapper = icalendar.Calendar()
                for comp in ical.walk("VEVENT"):
                    wrapper.add_component(comp)
                out.extend(_occurrences(wrapper, start, end, tz))
    return out


async def sync_source(src: CalendarSource, tz_name: str) -> dict:
    tz = ZoneInfo(tz_name)
    if src.type == "ics":
        events = await fetch_ics(src, tz)
    else:
        with session_scope() as db:
            pw = secrets_store.get_secret(db, secret_name(src.id)) or ""
        events = await asyncio.to_thread(_caldav_fetch, src, pw, tz)
    return {"count": len(events), "events": events}


def _event_id(source_id: str, ev: dict) -> str:
    return hashlib.sha1(f"{source_id}|{ev['uid']}|{ev['start']}".encode()).hexdigest()[:40]


def store_events(db: Session, source_id: str, events: list[dict]) -> bool:
    """Replace the cached occurrences of one source. Returns True when something changed."""
    new = {}
    for ev in events:
        new[_event_id(source_id, ev)] = ev
    old = {r.id: r for r in db.query(CalendarEvent).filter(CalendarEvent.source_id == source_id)}
    changed = set(new) != set(old)
    for eid, r in old.items():
        if eid not in new:
            db.delete(r)
        else:
            ev = new[eid]
            if (r.title, r.end, r.location, r.notes) != (ev["title"], ev["end"], ev["location"], ev["notes"]):
                changed = True
                r.title, r.end, r.location, r.notes = ev["title"], ev["end"], ev["location"], ev["notes"]
    for eid, ev in new.items():
        if eid not in old:
            db.add(CalendarEvent(id=eid, source_id=source_id, title=ev["title"], start=ev["start"], end=ev["end"],
                                 all_day=ev["all_day"], location=ev["location"], notes=ev["notes"]))
    db.flush()
    return changed


def _status(db: Session, key: str) -> SourceStatus:
    row = db.get(SourceStatus, key)
    if not row:
        row = SourceStatus(key=key, data={})
        db.add(row)
        db.flush()
    return row


async def run_sync(source_id: str) -> dict:
    """Sync one source now; never raises, records the outcome."""
    with session_scope() as db:
        g, _ = config_service.get_global(db)
        src = next((s for s in g.calendars if s.id == source_id), None)
        tz_name = g.general.timezone
    if not src:
        return {"ok": False, "detail": "Fuente desconocida"}
    key = f"calendar:{source_id}"
    try:
        res = await sync_source(src, tz_name)
        with session_scope() as db:
            changed = store_events(db, source_id, res["events"])
            st = _status(db, key)
            now = datetime.now(timezone.utc)
            st.ok, st.detail, st.last_success, st.last_attempt = True, f"{res['count']} eventos", now, now
            st.data = {"fails": 0}
        if changed:
            bus.publish("calendar.updated", {"source": source_id})
        return {"ok": True, "detail": f"{res['count']} eventos"}
    except Exception as exc:  # noqa: BLE001
        msg = _friendly(exc)
        log.warning("calendar sync %s failed: %s", source_id, msg)
        with session_scope() as db:
            st = _status(db, key)
            st.ok, st.detail, st.last_attempt = False, msg[:480], datetime.now(timezone.utc)
            st.data = {"fails": int((st.data or {}).get("fails", 0)) + 1}
        return {"ok": False, "detail": msg}


def _friendly(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"El servidor de calendario respondió {exc.response.status_code}"
    if isinstance(exc, httpx.HTTPError):
        return "No se pudo conectar con el calendario"
    name = exc.__class__.__name__
    if "Authorization" in name or "401" in str(exc):
        return "Credenciales de calendario rechazadas (usa una contraseña específica de aplicación)"
    return f"{name}: {exc}"[:300]


def due_sources() -> list[str]:
    now = datetime.now(timezone.utc)
    due = []
    with session_scope() as db:
        g, _ = config_service.get_global(db)
        for src in g.calendars:
            if not src.enabled:
                continue
            st = db.get(SourceStatus, f"calendar:{src.id}")
            if not st or not st.last_attempt:
                due.append(src.id)
                continue
            last = st.last_attempt if st.last_attempt.tzinfo else st.last_attempt.replace(tzinfo=timezone.utc)
            fails = int((st.data or {}).get("fails", 0))
            wait = src.refresh_minutes if fails == 0 else min(src.refresh_minutes, 2 ** min(fails, 6))
            if now - last >= timedelta(minutes=wait):
                due.append(src.id)
    return due


async def scheduler_loop() -> None:
    while True:
        try:
            for sid in due_sources():
                await run_sync(sid)
        except Exception:  # noqa: BLE001
            log.exception("calendar scheduler error")
        await asyncio.sleep(60)


_LEGACY_TABLE = str.maketrans(LEGACY_EMOJI)


def modern_emoji(text: str) -> str:
    """Swap the private-use emoji codes of very old phones for the standard ones that fonts can draw."""
    return text.translate(_LEGACY_TABLE) if text else text


USER_TAG = re.compile(r"@user:\s*([^\s,;@]+)", re.IGNORECASE)
FAMILY_WORDS = {"familia", "family", "todos", "all"}


def _fold(text: str) -> str:
    """Lower case without accents, so `@user:ines` finds a person called "Inés"."""
    decomposed = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def read_user_tags(notes: str, people: list) -> tuple[list[str] | None, str]:
    """Look for `@user:<name>` tags in an event's notes.

    Returns the matching person ids (an empty list when the tag asks for the whole family) or None when the
    notes carry no usable tag, plus the notes with every tag removed. A tag matches a person's id, full name
    or first name, ignoring case and accents.
    """
    tags = USER_TAG.findall(notes or "")
    if not tags:
        return None, notes
    keys: dict[str, str] = {}
    for p in people:
        for key in (p.id, p.name, p.name.split()[0] if p.name.split() else ""):
            keys.setdefault(_fold(key), p.id)
    found: list[str] = []
    family = False
    for tag in tags:
        folded = _fold(tag)
        if folded in FAMILY_WORDS:
            family = True
        elif folded in keys and keys[folded] not in found:
            found.append(keys[folded])
    cleaned = re.sub(r"[ \t]{2,}", " ", USER_TAG.sub("", notes)).strip()
    if found:
        return found, cleaned
    return ([] if family else None), cleaned


def device_events(db: Session, person_ids_visible: list[str] | None = None) -> list[dict]:
    """Events for the frames. Who an event belongs to is, in order: an `@user:` tag in its notes, the people
    linked to its calendar, or nobody. An event with nobody is a family event: it appears in the agendas and
    as "next up", but under no person's column."""
    g, _ = config_service.get_global(db)
    all_people = [p.id for p in g.people]
    by_source = {s.id: [p for p in s.person_ids if p in all_people] for s in g.calendars if s.enabled}
    out = []
    for r in db.query(CalendarEvent).filter(CalendarEvent.source_id.in_(list(by_source) or [""])):
        tagged, notes = read_user_tags(r.notes, g.people)
        people = by_source[r.source_id] if tagged is None else tagged
        if people and person_ids_visible:
            people = [p for p in people if p in person_ids_visible]
            if not people:
                continue
        out.append({"id": r.id, "title": modern_emoji(r.title), "start": r.start, "end": r.end, "allDay": r.all_day,
                    "loc": modern_emoji(r.location), "notes": modern_emoji(notes), "people": people})
    return out
