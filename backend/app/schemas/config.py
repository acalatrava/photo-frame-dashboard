"""Versioned configuration schemas.

`GlobalConfig` holds server-wide settings; `DeviceConfig` is what one frame gets. Secrets
(Home Assistant token, CalDAV passwords) never appear here: they live in the encrypted store.
"""
import re
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = 1
# Light-sensor defaults. The first release used 8 lux / 25 %, far too coarse for the frame's sensor.
OLD_ABS, OLD_REL = 8, 0.25
NEW_ABS, NEW_REL = 2.5, 0.05
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,30}$")
ENTITY_ID = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Location(Strict):
    name: str = Field("", max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


# Screens that can be reordered in the side rail. Today is always first and Settings always last.
NAV_ITEMS = ["calendar", "photos", "chores", "house", "cameras", "shopping", "menu", "music"]


def normalize_nav(order: list[str]) -> list[str]:
    """The given order first, then any screen that was left out, in the default order."""
    seen = [i for i in dict.fromkeys(order) if i in NAV_ITEMS]
    return seen + [i for i in NAV_ITEMS if i not in seen]


class GeneralConfig(Strict):
    language: Literal["es-ES", "en"] = "es-ES"
    timezone: str = "Europe/Madrid"
    location: Location | None = None
    nav_order: list[str] = []

    @field_validator("nav_order")
    @classmethod
    def _nav(cls, v: list[str]) -> list[str]:
        if any(i not in NAV_ITEMS for i in v):
            raise ValueError("pantalla desconocida")
        return normalize_nav(v)

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("zona horaria desconocida") from exc
        return v


class Person(Strict):
    id: str
    name: str = Field(min_length=1, max_length=40)
    color: str = "#2D5BFF"
    ha_person: str | None = None

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not SLUG.match(v):
            raise ValueError("id inválido")
        return v

    @field_validator("color")
    @classmethod
    def _color(cls, v: str) -> str:
        if not HEX_COLOR.match(v):
            raise ValueError("color debe ser #RRGGBB")
        return v

    @field_validator("ha_person")
    @classmethod
    def _ha(cls, v):
        if v and not ENTITY_ID.match(v):
            raise ValueError("entity_id inválido")
        return v or None


class CalendarSource(Strict):
    id: str
    name: str = Field(min_length=1, max_length=60)
    type: Literal["ics", "caldav"] = "ics"
    url: str = Field(max_length=500)
    username: str = Field("", max_length=120)
    # CalDAV only: restrict to one calendar display name; empty means every calendar of the account.
    calendar_name: str = Field("", max_length=120)
    person_ids: list[str] = []
    enabled: bool = True
    refresh_minutes: int = Field(15, ge=5, le=1440)

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not SLUG.match(v):
            raise ValueError("id inválido")
        return v

    @field_validator("url")
    @classmethod
    def _url(cls, v: str) -> str:
        v = v.strip()
        if v.startswith("webcal://"):
            v = "https://" + v[len("webcal://"):]
        if not re.match(r"^https?://", v):
            raise ValueError("la URL debe ser http(s) o webcal")
        return v


ICONS = {"bulb", "lock", "unlock", "garage", "blinds", "thermo", "camera", "music", "heart", "star", "car", "drop",
         "box", "door", "bell", "play", "clock", "person", "bolt", "film", "utensils", "sunrise", "away", "sun", "moon",
         "home", "tasks", "cart", "cloud", "trash", "broom", "bed", "book", "paw", "plant", "shirt", "dish", "bath", "tv",
         "power", "window"}


class EntityMeta(Strict):
    """Display overrides for one Home Assistant entity (all optional)."""
    name: str = Field("", max_length=40)
    icon: str = ""
    color: str = ""

    @field_validator("icon")
    @classmethod
    def _icon(cls, v: str) -> str:
        if v and v not in ICONS:
            raise ValueError("icono desconocido")
        return v

    @field_validator("color")
    @classmethod
    def _color(cls, v: str) -> str:
        if v and not HEX_COLOR.match(v):
            raise ValueError("color debe ser #RRGGBB")
        return v


class HomeAssistantConfig(Strict):
    enabled: bool = False
    url: str = Field("", max_length=300)
    verify_tls: bool = True
    # Only these entities can be read by the frames and controlled from them.
    authorized_entities: list[str] = []
    entity_meta: dict[str, EntityMeta] = {}

    @field_validator("url")
    @classmethod
    def _url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if v and not re.match(r"^https?://", v):
            raise ValueError("la URL debe empezar por http:// o https://")
        return v

    @field_validator("entity_meta")
    @classmethod
    def _meta_keys(cls, v: dict[str, EntityMeta]) -> dict[str, EntityMeta]:
        for k in v:
            if not ENTITY_ID.match(k):
                raise ValueError(f"entity_id inválido: {k}")
        return v

    @field_validator("authorized_entities")
    @classmethod
    def _ents(cls, v: list[str]) -> list[str]:
        for e in v:
            if not ENTITY_ID.match(e):
                raise ValueError(f"entity_id inválido: {e}")
        return list(dict.fromkeys(v))


class Chore(Strict):
    """A recurring task. With no people it is one shared check for the whole family."""
    id: str
    title: str = Field(min_length=1, max_length=80)
    icon: str = "tasks"
    person_ids: list[str] = []
    # Weekdays (0 = Monday .. 6 = Sunday). Empty means every day.
    days: list[int] = []
    # Which weeks it repeats: every week, ISO-even / ISO-odd weeks, or every N weeks counting from the week that
    # contains `start_date`.
    # "once" is a one-off task: `start_date` is the day it is due, and it stays on the list until somebody ticks it.
    week_mode: Literal["all", "even", "odd", "every", "once"] = "all"
    every_weeks: int = Field(2, ge=2, le=12)
    start_date: str = ""
    time: str = ""
    enabled: bool = True

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not SLUG.match(v):
            raise ValueError("id inválido")
        return v

    @field_validator("icon")
    @classmethod
    def _icon(cls, v: str) -> str:
        if v not in ICONS:
            raise ValueError("icono desconocido")
        return v

    @field_validator("start_date")
    @classmethod
    def _start(cls, v: str) -> str:
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError("fecha AAAA-MM-DD") from exc
        return v

    @model_validator(mode="after")
    def _every_needs_start(self):
        if self.week_mode == "every" and not self.start_date:
            raise ValueError("indica la semana de inicio")
        if self.week_mode == "once" and not self.start_date:
            raise ValueError("indica el día de la tarea")
        return self

    @field_validator("days")
    @classmethod
    def _days(cls, v: list[int]) -> list[int]:
        if any(d < 0 or d > 6 for d in v):
            raise ValueError("día de la semana inválido")
        return sorted(set(v))

    @field_validator("time")
    @classmethod
    def _time(cls, v: str) -> str:
        if v and not HHMM.match(v):
            raise ValueError("hora HH:MM")
        return v


class FrigateConfig(Strict):
    url: str = Field("", max_length=300)
    verify_tls: bool = True

    @field_validator("url")
    @classmethod
    def _url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if v and not re.match(r"^https?://", v):
            raise ValueError("la URL debe empezar por http:// o https://")
        return v


class CameraSource(Strict):
    id: str
    name: str = Field(min_length=1, max_length=40)
    source: Literal["frigate", "ha", "url"] = "frigate"
    frigate_camera: str = Field("", max_length=80)
    ha_entity: str | None = None
    url: str = Field("", max_length=500)
    fps: int = Field(5, ge=1, le=10)
    enabled: bool = True

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not SLUG.match(v):
            raise ValueError("id inválido")
        return v

    @field_validator("ha_entity")
    @classmethod
    def _ha(cls, v):
        if v and not re.match(r"^camera\.[a-z0-9_]+$", v):
            raise ValueError("debe ser una entidad camera.*")
        return v or None

    @field_validator("url")
    @classmethod
    def _url(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r"^https?://", v):
            raise ValueError("la URL debe empezar por http:// o https://")
        return v

    @field_validator("frigate_camera")
    @classmethod
    def _fc(cls, v: str) -> str:
        if v and not re.match(r"^[A-Za-z0-9_.-]+$", v):
            raise ValueError("nombre de cámara de Frigate inválido")
        return v


class ShoppingConfig(Strict):
    provider: Literal["local", "homeassistant"] = "local"
    ha_entity: str | None = None

    @field_validator("ha_entity")
    @classmethod
    def _e(cls, v):
        if v and not v.startswith("todo."):
            raise ValueError("la lista debe ser una entidad todo.*")
        return v or None


class DisplayConfig(Strict):
    brightness_mode: Literal["automatic", "manual", "always_on"] = "automatic"
    brightness_min: int = Field(15, ge=1, le=100)
    brightness_max: int = Field(100, ge=1, le=100)
    inactivity_timeout: int = Field(60, ge=10, le=3600)
    screen_off: Literal["never", "black", "off"] = "black"
    night_mode: bool = True
    night_start: str = "22:00"
    night_end: str = "07:00"
    night_brightness: int = Field(5, ge=0, le=100)
    # Colour of the clock on the dim night screen.
    night_color: str = "#C22C1C"

    @field_validator("night_start", "night_end")
    @classmethod
    def _t(cls, v: str) -> str:
        if not HHMM.match(v):
            raise ValueError("hora HH:MM")
        return v

    @field_validator("night_color")
    @classmethod
    def _color(cls, v: str) -> str:
        if not HEX_COLOR.match(v):
            raise ValueError("color debe ser #RRGGBB")
        return v


class PresenceConfig(Strict):
    enabled: bool = True
    provider: Literal["light_sensor", "homeassistant", "combined", "none"] = "light_sensor"
    sensitivity: Literal["low", "medium", "high"] = "medium"
    ha_entities: list[str] = []
    ha_hold_seconds: int = Field(120, ge=10, le=3600)
    # Tuning knobs for the light heuristic (see docs/light-sensor.md).
    min_abs_lux: float = Field(NEW_ABS, ge=0, le=500)
    min_rel_change: float = Field(NEW_REL, ge=0.02, le=2)
    min_event_gap_s: float = Field(2.0, ge=0.2, le=60)
    activity_hold_s: int = Field(45, ge=5, le=1800)
    # Someone switched the room light off: the lux reading collapses within seconds. The screen goes to sleep then.
    sleep_on_lights_off: bool = True
    lights_off_lux: float = Field(10, ge=1, le=50)


PHOTO_WIDGETS = ["time", "date", "weather", "calendar", "tasks", "people"]


class PhotosConfig(Strict):
    enabled: bool = True
    album_id: str | None = None
    interval_s: int = Field(30, ge=5, le=3600)
    order: Literal["chronological", "random"] = "random"
    fit: Literal["contain", "cover"] = "cover"
    # Caption on the photo itself (when and where it was taken).
    show_overlay: bool = True
    # Information drawn over the photos while the frame is idle.
    widgets: list[Literal["time", "date", "weather", "calendar", "tasks", "people"]] = [
        "time", "date", "weather", "calendar", "people"]
    cache_limit: int = Field(80, ge=10, le=400)
    # Colour of the clock, date and weather drawn over the photos while the frame is idle.
    text_color: str = "#FFFFFF"
    # How one photo gives way to the next.
    transition: Literal["fade", "none"] = "fade"

    @field_validator("text_color")
    @classmethod
    def _text_color(cls, v: str) -> str:
        if not HEX_COLOR.match(v):
            raise ValueError("color debe ser #RRGGBB")
        return v

    @field_validator("widgets")
    @classmethod
    def _widgets(cls, v: list[str]) -> list[str]:
        return [w for w in PHOTO_WIDGETS if w in v]


SOUNDS = ["chime", "bell", "soft", "beep", "melody", "none"]


class ChimeConfig(Strict):
    """A sound on the hour (or half hour) with a quiet period in which the frame stays silent."""
    enabled: bool = False
    every: Literal["hour", "half"] = "hour"
    sound: Literal["chime", "bell", "soft", "speak"] = "chime"
    quiet: bool = True
    quiet_start: str = "22:00"
    quiet_end: str = "08:00"

    @field_validator("quiet_start", "quiet_end")
    @classmethod
    def _t(cls, v: str) -> str:
        if not HHMM.match(v):
            raise ValueError("hora HH:MM")
        return v


class SoundsConfig(Strict):
    # Master volume of the frame (Android media volume, 0 to 100).
    volume: int = Field(70, ge=0, le=100)
    chime: ChimeConfig = ChimeConfig()


class HomeLayoutConfig(Strict):
    default_view: Literal["home", "calendar", "photos", "house", "chores", "cameras", "shopping", "menu", "music", "settings"] = "home"
    # How the calendar opens; whoever is at the frame can still switch it.
    calendar_mode: Literal["day", "3day", "week", "month"] = "day"
    ambient_after_s: int = Field(120, ge=15, le=3600)
    home_after_s: int = Field(60, ge=10, le=3600)
    person_ids: list[str] = []
    entity_order: list[str] = []


class DeviceConfig(Strict):
    schema_version: int = SCHEMA_VERSION
    room: str = Field("", max_length=60)
    display: DisplayConfig = DisplayConfig()
    presence: PresenceConfig = PresenceConfig()
    photos: PhotosConfig = PhotosConfig()
    layout: HomeLayoutConfig = HomeLayoutConfig()
    sounds: SoundsConfig = SoundsConfig()
    language: Literal["es-ES", "en", "inherit"] = "inherit"


MEALS = ["breakfast", "midmorning", "lunch", "snack", "dinner"]
MAX_MENU_WEEKS = 12


class MenuDay(Strict):
    """What is served at each meal of one day. Empty means nothing planned."""
    breakfast: str = Field("", max_length=300)
    midmorning: str = Field("", max_length=300)
    lunch: str = Field("", max_length=300)
    snack: str = Field("", max_length=300)
    dinner: str = Field("", max_length=300)


def _blank_days() -> list["MenuDay"]:
    return [MenuDay() for _ in range(7)]


class MenuWeek(Strict):
    name: str = Field("", max_length=40)
    # Monday first. Seven entries, always.
    days: list[MenuDay] = Field(default_factory=_blank_days)
    # A meal that is the same all week (like "fruit plus one snack") is written once here and spans the day columns.
    shared: MenuDay = MenuDay()

    @field_validator("days")
    @classmethod
    def _seven(cls, v: list[MenuDay]) -> list[MenuDay]:
        if len(v) != 7:
            raise ValueError("una semana tiene siete días (de lunes a domingo)")
        return v


class MenuConfig(Strict):
    """A rotating weekly menu. The weeks repeat in order; `start_week` was the current one during the week that
    begins on `start_date`, which is how the frame knows which week it is today."""
    meals: list[Literal["breakfast", "midmorning", "lunch", "snack", "dinner"]] = ["breakfast", "lunch", "dinner"]
    weeks: list[MenuWeek] = Field(default_factory=list, max_length=MAX_MENU_WEEKS)
    start_week: int = Field(1, ge=1, le=MAX_MENU_WEEKS)
    start_date: str = ""

    @field_validator("meals")
    @classmethod
    def _meals(cls, v: list[str]) -> list[str]:
        return [m for m in MEALS if m in v]

    @field_validator("start_date")
    @classmethod
    def _start(cls, v: str) -> str:
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError("fecha AAAA-MM-DD") from exc
        return v

    @model_validator(mode="after")
    def _clamp_start_week(self):
        if self.weeks and self.start_week > len(self.weeks):
            self.start_week = len(self.weeks)
        return self


class Alarm(Strict):
    """Goes off on the frames at a given time: a sound, a message (optionally read aloud), or both."""
    id: str
    name: str = Field("", max_length=40)
    time: str = "07:00"
    # Weekdays (0 = Monday .. 6 = Sunday). Empty means every day. Ignored when `date` is set.
    days: list[int] = []
    # A one-off alarm for a single day (AAAA-MM-DD).
    date: str = ""
    enabled: bool = True
    sound: Literal["chime", "bell", "soft", "beep", "melody", "none"] = "melody"
    message: str = Field("", max_length=200)
    speak: bool = False
    volume: int = Field(80, ge=1, le=100)
    # The alarm stops by itself after this long if nobody touches the frame.
    duration_s: int = Field(60, ge=5, le=900)
    # Minutes a snooze lasts; 0 hides the snooze button.
    snooze_min: int = Field(5, ge=0, le=60)
    # Frames it rings on; empty means all of them.
    device_ids: list[str] = []

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        if not SLUG.match(v):
            raise ValueError("id inválido")
        return v

    @field_validator("time")
    @classmethod
    def _time(cls, v: str) -> str:
        if not HHMM.match(v):
            raise ValueError("hora HH:MM")
        return v

    @field_validator("days")
    @classmethod
    def _days(cls, v: list[int]) -> list[int]:
        if any(d < 0 or d > 6 for d in v):
            raise ValueError("día de la semana inválido")
        return sorted(set(v))

    @field_validator("date")
    @classmethod
    def _date(cls, v: str) -> str:
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError("fecha AAAA-MM-DD") from exc
        return v

    @model_validator(mode="after")
    def _has_something(self):
        if self.sound == "none" and not self.message.strip():
            raise ValueError("una alarma necesita un sonido o un mensaje")
        return self


class UpdatesConfig(Strict):
    """off: frames ignore published app versions; notify: they offer the update in Settings;
    auto: they also download it in the background so installing is a single tap."""
    mode: Literal["off", "notify", "auto"] = "notify"


class SpotifyConfig(Strict):
    """The frames control Spotify Connect speakers through the account linked here."""
    enabled: bool = False
    # From a free app created at developer.spotify.com. With PKCE no client secret is needed.
    client_id: str = Field("", max_length=64, pattern=r"^[A-Za-z0-9]*$")
    # Spotify only accepts https or loopback addresses; the page it lands on does not need to exist.
    redirect_uri: str = Field("http://127.0.0.1:8787/callback", max_length=200)

    @field_validator("redirect_uri")
    @classmethod
    def _redirect(cls, v: str) -> str:
        if not (v.startswith("https://") or v.startswith("http://127.0.0.1") or v.startswith("http://[::1]")):
            raise ValueError("Spotify solo admite https o una dirección local http://127.0.0.1")
        return v


class GlobalConfig(Strict):
    schema_version: int = SCHEMA_VERSION
    general: GeneralConfig = GeneralConfig()
    people: list[Person] = []
    calendars: list[CalendarSource] = []
    homeassistant: HomeAssistantConfig = HomeAssistantConfig()
    shopping: ShoppingConfig = ShoppingConfig()
    chores: list[Chore] = []
    frigate: FrigateConfig = FrigateConfig()
    cameras: list[CameraSource] = []
    updates: UpdatesConfig = UpdatesConfig()
    menu: MenuConfig = MenuConfig()
    alarms: list[Alarm] = Field(default_factory=list, max_length=50)
    spotify: SpotifyConfig = SpotifyConfig()
    device_defaults: DeviceConfig = DeviceConfig()

    @field_validator("people")
    @classmethod
    def _unique(cls, v: list[Person]) -> list[Person]:
        ids = [p.id for p in v]
        if len(ids) != len(set(ids)):
            raise ValueError("ids de personas duplicados")
        return v

    @field_validator("chores")
    @classmethod
    def _unique_chores(cls, v: list[Chore]) -> list[Chore]:
        ids = [c.id for c in v]
        if len(ids) != len(set(ids)):
            raise ValueError("ids de tareas duplicados")
        return v

    @field_validator("alarms")
    @classmethod
    def _unique_alarms(cls, v: list[Alarm]) -> list[Alarm]:
        ids = [a.id for a in v]
        if len(ids) != len(set(ids)):
            raise ValueError("ids de alarmas duplicados")
        return v

    @field_validator("cameras")
    @classmethod
    def _unique_cameras(cls, v: list[CameraSource]) -> list[CameraSource]:
        ids = [c.id for c in v]
        if len(ids) != len(set(ids)):
            raise ValueError("ids de cámaras duplicados")
        return v


def migrate_device(raw: dict) -> dict:
    """Replace the old coarse light-sensor defaults when the owner never changed them."""
    raw = dict(raw or {})
    p = dict(raw.get("presence") or {})
    if p.get("min_abs_lux") == OLD_ABS and p.get("min_rel_change") == OLD_REL:
        p["min_abs_lux"], p["min_rel_change"] = NEW_ABS, NEW_REL
        raw["presence"] = p
    return raw


def migrate_global(raw: dict) -> dict:
    """Upgrade stored documents to SCHEMA_VERSION. Version 1 is the first schema."""
    raw = dict(raw or {})
    raw.setdefault("schema_version", SCHEMA_VERSION)
    if isinstance(raw.get("device_defaults"), dict):
        raw["device_defaults"] = migrate_device(raw["device_defaults"])
    return raw
