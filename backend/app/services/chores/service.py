"""Household chores: recurring tasks assigned to people (or shared) and ticked off from the frames.

A chore is due on certain weekdays (all of them when none are set). A one-off chore ("once") has a due day and stays
on the list until it is ticked, then disappears from the next day on. Every assigned person has their own check
for the day; a chore without people is one shared check. Completion is stored per local day, so the next day
starts clean without any reset job. Ticking is an absolute state ("done" or "not done"): the last write wins.
"""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from ...core.events import bus
from ...models import ChoreLog
from ...schemas.config import Chore, GlobalConfig

KEEP_DAYS = 120


class ChoreError(Exception):
    def __init__(self, status: int, msg: str):
        super().__init__(msg)
        self.status, self.msg = status, msg


def local_day(g: GlobalConfig, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.astimezone(ZoneInfo(g.general.timezone)).date().isoformat()


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def is_due(chore: Chore, day: str) -> bool:
    if not chore.enabled:
        return False
    d = datetime.strptime(day, "%Y-%m-%d").date()
    if chore.week_mode == "once":
        return day >= chore.start_date
    if chore.days and d.weekday() not in chore.days:
        return False
    if chore.week_mode == "even":
        return d.isocalendar().week % 2 == 0
    if chore.week_mode == "odd":
        return d.isocalendar().week % 2 == 1
    if chore.week_mode == "every":
        start = datetime.strptime(chore.start_date, "%Y-%m-%d").date()
        return ((_monday(d) - _monday(start)).days // 7) % chore.every_weeks == 0
    return True


def slots(chore: Chore, valid_people: set[str]) -> list[str]:
    """Person ids that have their own check; [""] for a shared chore."""
    people = [p for p in chore.person_ids if p in valid_people]
    return people or [""]


def snapshot(db: Session, g: GlobalConfig, day: str | None = None) -> dict:
    day = day or local_day(g)
    valid = {p.id for p in g.people}
    done = {(r.chore_id, r.person_id) for r in db.query(ChoreLog).filter(ChoreLog.day == day)}
    once_ids = [c.id for c in g.chores if c.week_mode == "once"]
    finished = {}
    if once_ids:
        for r in db.query(ChoreLog).filter(ChoreLog.chore_id.in_(once_ids)):
            key = (r.chore_id, r.person_id)
            finished[key] = min(finished.get(key, r.day), r.day)
    items = []
    for c in g.chores:
        if not is_due(c, day):
            continue
        once = c.week_mode == "once"
        for pid in slots(c, valid):
            # A one-off chore ticked on an earlier day is finished and no longer shown.
            if once and finished.get((c.id, pid), day) < day:
                continue
            items.append({"id": c.id, "title": c.title, "icon": c.icon, "person_id": pid or None,
                          "time": c.time or None, "done": (c.id, pid) in done,
                          "once": once, "overdue": once and c.start_date < day and (c.id, pid) not in done})
    items.sort(key=lambda i: (not i["overdue"], i["time"] or "99:99", i["title"].lower()))
    return {"day": day, "configured": sum(1 for c in g.chores if c.enabled), "items": items}


def set_done(db: Session, g: GlobalConfig, chore_id: str, person_id: str, done: bool, device_id: str | None,
             day: str | None = None) -> dict:
    today = local_day(g)
    day = day or today
    # A frame that was offline may replay yesterday's ticks, but nothing older or in the future.
    allowed = {today, (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=1)).date().isoformat()}
    if day not in allowed:
        raise ChoreError(422, "Día no permitido")
    chore = next((c for c in g.chores if c.id == chore_id), None)
    if not chore:
        raise ChoreError(404, "Tarea no encontrada")
    valid = {p.id for p in g.people}
    if person_id not in slots(chore, valid):
        raise ChoreError(422, "Esa persona no tiene asignada la tarea")
    row = (db.query(ChoreLog).filter(ChoreLog.chore_id == chore_id, ChoreLog.day == day,
                                     ChoreLog.person_id == person_id).first())
    if done and not row:
        db.add(ChoreLog(chore_id=chore_id, day=day, person_id=person_id, done_by_device=device_id))
    elif not done and row:
        db.delete(row)
    db.flush()
    bus.publish("chores.changed", {"day": day, "by": device_id})
    return snapshot(db, g, today)


def purge_old(db: Session, g: GlobalConfig) -> int:
    cutoff = (datetime.strptime(local_day(g), "%Y-%m-%d") - timedelta(days=KEEP_DAYS)).date().isoformat()
    n = db.query(ChoreLog).filter(ChoreLog.day < cutoff).delete()
    return n


def week_stats(db: Session, g: GlobalConfig) -> dict:
    """Per person: checks done / due over the last 7 local days (today included)."""
    today = datetime.strptime(local_day(g), "%Y-%m-%d")
    days = [(today - timedelta(days=i)).date().isoformat() for i in range(7)]
    valid = {p.id for p in g.people}
    done = {(r.chore_id, r.person_id, r.day) for r in db.query(ChoreLog).filter(ChoreLog.day.in_(days))}
    once_done = {(r.chore_id, r.person_id) for r in
                 db.query(ChoreLog).filter(ChoreLog.chore_id.in_([c.id for c in g.chores if c.week_mode == "once"]))}
    out: dict[str, dict] = {}
    for c in g.chores:
        for d in days:
            if c.week_mode == "once":
                if d != c.start_date or not c.enabled:
                    continue
                for pid in slots(c, valid):
                    o = out.setdefault(pid or "", {"done": 0, "due": 0})
                    o["due"] += 1
                    o["done"] += 1 if (c.id, pid) in once_done else 0
                continue
            if not is_due(c, d):
                continue
            for pid in slots(c, valid):
                o = out.setdefault(pid or "", {"done": 0, "due": 0})
                o["due"] += 1
                o["done"] += 1 if (c.id, pid, d) in done else 0
    return out
