"""Weekly menu: which week of the rotation applies on a given day."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from ...schemas.config import GlobalConfig, MenuConfig


def monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def today_in(tz_name: str, now: datetime | None = None) -> date:
    return (now or datetime.now(ZoneInfo("UTC"))).astimezone(ZoneInfo(tz_name)).date()


def week_index(menu: MenuConfig, day: date) -> int | None:
    """Zero-based position in `menu.weeks` for the week that contains `day`, or None with no weeks."""
    if not menu.weeks:
        return None
    anchor = monday(date.fromisoformat(menu.start_date)) if menu.start_date else monday(day)
    elapsed = (monday(day) - anchor).days // 7
    return (menu.start_week - 1 + elapsed) % len(menu.weeks)


def describe(menu: MenuConfig, day: date) -> dict:
    """The current and next week for admin screens and agents."""
    idx = week_index(menu, day)
    if idx is None:
        return {"configured": False, "today": day.isoformat(), "current": None, "next": None}
    nxt = (idx + 1) % len(menu.weeks)

    def one(i: int, start: date) -> dict:
        return {"number": i + 1, "name": menu.weeks[i].name, "starts": start.isoformat()}

    return {"configured": True, "today": day.isoformat(), "weekday": day.weekday(),
            "current": one(idx, monday(day)), "next": one(nxt, monday(day) + timedelta(days=7))}


def set_current_week(menu: MenuConfig, number: int, day: date) -> MenuConfig:
    """Declare that the week containing `day` is week `number` of the rotation."""
    if not menu.weeks:
        raise ValueError("Todavía no hay semanas en el menú")
    if not 1 <= number <= len(menu.weeks):
        raise ValueError(f"La semana debe estar entre 1 y {len(menu.weeks)}")
    return menu.model_copy(update={"start_week": number, "start_date": monday(day).isoformat()})


def for_frame(g: GlobalConfig, now: datetime | None = None) -> dict:
    """What a frame needs: the whole rotation, so it keeps working offline across a Monday."""
    m = g.menu
    return {"configured": bool(m.weeks), "meals": m.meals, "weeks": [w.model_dump(mode="json") for w in m.weeks],
            "start_week": m.start_week, "start_date": m.start_date or monday(today_in(g.general.timezone, now)).isoformat()}
