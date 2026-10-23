"""The tools an agent can call. Names are verbs; descriptions say what changes and what to call next."""
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from ..schemas.config import DeviceConfig, GlobalConfig, MAX_MENU_WEEKS, MEALS
from .runtime import Ctx, ToolError, merge_patch, q

Handler = Callable[[Ctx, dict], Awaitable[Any]]
A = "/api/v1/admin"


@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    handler: Handler
    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False

    def listing(self) -> dict:
        return {"name": self.name, "description": self.description, "inputSchema": self.schema,
                "annotations": {"readOnlyHint": self.read_only, "destructiveHint": self.destructive,
                                "idempotentHint": self.idempotent, "openWorldHint": False}}


TOOLS: dict[str, Tool] = {}


def obj(props: dict | None = None, required: tuple | list = ()) -> dict:
    return {"type": "object", "properties": props or {}, "required": list(required), "additionalProperties": False}


S = {"type": "string"}
I = {"type": "integer"}
DEV = {"type": "string", "description": "Id del marco (ver list_devices)."}
MEAL_PROPS = {m: {"type": "string", "maxLength": 300} for m in MEALS}


def register(name: str, description: str, schema: dict, handler: Handler, **flags: bool) -> None:
    TOOLS[name] = Tool(name, description, schema, handler, **flags)


def rest(name: str, description: str, method: str, path: str, props: dict | None = None, required: tuple = (),
         query: tuple = (), body: str | None = None, **flags: bool) -> None:
    """A tool that is one admin API call. `path` may hold {placeholders}; `body` names the argument sent as the
    JSON body (when empty, every argument that is not a path or query parameter becomes the body)."""
    props = props or {}

    async def run(ctx: Ctx, args: dict) -> Any:
        used = {k: args[k] for k in args}
        url = path
        for key in re.findall(r"{(\w+)}", path):
            url = url.replace("{" + key + "}", q(used.pop(key)))
        params = {k: used.pop(k) for k in query if k in used}
        payload = None
        if body:
            payload = used.pop(body, None)
        elif method in ("POST", "PUT", "PATCH") and (used or props):
            payload = used
        elif method in ("POST", "PUT", "PATCH"):
            payload = {}
        return await ctx.api(method, url, params=params or None, body=payload)

    flags.setdefault("read_only", method == "GET")
    register(name, description, obj(props, required), run, **flags)


# ------------------------------------------------------------------ overview and configuration
rest("get_status", "Resumen de salud: versión, Home Assistant, calendarios, tiempo y número de marcos.", "GET",
     f"{A}/status")
rest("get_config", "Configuración global completa (general, personas, calendarios, Home Assistant, compra, tareas, "
     "cámaras, actualizaciones, menú y valores por defecto de los marcos) y qué secretos están guardados. "
     "Los secretos nunca se devuelven.", "GET", f"{A}/config")


async def _schema(ctx: Ctx, args: dict) -> Any:
    return {"global": GlobalConfig.model_json_schema(), "device": DeviceConfig.model_json_schema()}


register("get_config_schema", "JSON Schema de la configuración global y de la de un marco: nombres de campos, tipos, "
         "valores permitidos y límites. Léelo antes de escribir configuración.", obj(), _schema, read_only=True)


async def _update_config(ctx: Ctx, args: dict) -> Any:
    cur = (await ctx.api("GET", f"{A}/config"))["config"]
    merged = merge_patch(cur, args["patch"])
    res = await ctx.api("PUT", f"{A}/config", body=merged)
    return {"version": res["version"], "changed_sections": sorted(args["patch"])}


register("update_config", "Cambia parte de la configuración global con un JSON Merge Patch (RFC 7386): los objetos se "
         "fusionan, un valor null elimina la clave y las listas se REEMPLAZAN enteras (para personas, calendarios, "
         "tareas y cámaras usa upsert_collection_item). Ejemplo: {\"general\":{\"nav_order\":[\"calendar\",\"menu\"]}}. "
         "Se valida entera y los marcos reciben el cambio al instante.",
         obj({"patch": {"type": "object"}}, ["patch"]), _update_config, idempotent=True)

COLLECTIONS = {"people": "name", "calendars": "name", "chores": "title", "cameras": "name"}


def _slug(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return (re.sub(r"[^a-z0-9]+", "-", plain).strip("-") or "item")[:24]


async def _upsert(ctx: Ctx, args: dict) -> Any:
    coll = args["collection"]
    cfg = (await ctx.api("GET", f"{A}/config"))["config"]
    items = cfg[coll]
    item = dict(args["item"])
    if not item.get("id"):
        base = _slug(str(item.get(COLLECTIONS[coll], "")))
        taken = {i["id"] for i in items}
        item["id"], n = base, 2
        while item["id"] in taken:
            item["id"], n = f"{base}-{n}", n + 1
    existing = next((i for i in items if i["id"] == item["id"]), None)
    if existing:
        merged = {**existing, **item}
        cfg[coll] = [merged if i["id"] == item["id"] else i for i in items]
    else:
        merged = item
        cfg[coll] = items + [item]
    res = await ctx.api("PUT", f"{A}/config", body=cfg)
    return {"created": existing is None, "item": merged, "version": res["version"]}


register("upsert_collection_item", "Crea o actualiza un elemento de people, calendars, chores o cameras. Si `item.id` "
         "existe se fusionan solo los campos que envíes; si no existe se crea (el id se genera desde el nombre si "
         "falta). Consulta get_config_schema para los campos de cada tipo. Los secretos (contraseña de un calendario) "
         "se guardan aparte con set_calendar_password.",
         obj({"collection": {"type": "string", "enum": list(COLLECTIONS)}, "item": {"type": "object"}},
             ["collection", "item"]), _upsert, idempotent=True)


async def _delete_item(ctx: Ctx, args: dict) -> Any:
    coll, ident = args["collection"], args["id"]
    cfg = (await ctx.api("GET", f"{A}/config"))["config"]
    if not any(i["id"] == ident for i in cfg[coll]):
        raise ToolError(f"No hay ningún elemento con id {ident} en {coll}")
    cfg[coll] = [i for i in cfg[coll] if i["id"] != ident]
    if coll == "people":
        for other in ("calendars", "chores"):
            for i in cfg[other]:
                i["person_ids"] = [p for p in i["person_ids"] if p != ident]
    res = await ctx.api("PUT", f"{A}/config", body=cfg)
    return {"deleted": ident, "version": res["version"]}


register("delete_collection_item", "Elimina un elemento de people, calendars, chores o cameras por id. Al borrar una "
         "persona se quita también de los calendarios y tareas que la nombraban.",
         obj({"collection": {"type": "string", "enum": list(COLLECTIONS)}, "id": S}, ["collection", "id"]),
         _delete_item, destructive=True)

# ------------------------------------------------------------------ frames
rest("list_devices", "Marcos emparejados: estado, conexión, versión de la app y última vez visto.", "GET",
     f"{A}/devices")
rest("get_device", "Un marco con su configuración completa (pantalla, presencia, fotos, diseño).", "GET",
     f"{A}/devices/{{device_id}}", {"device_id": DEV}, ("device_id",))


async def _update_device(ctx: Ctx, args: dict) -> Any:
    did = q(args["device_id"])
    cur = await ctx.api("GET", f"{A}/devices/{did}")
    body: dict = {}
    if args.get("name"):
        body["name"] = args["name"]
    if args.get("config_patch"):
        body["config"] = merge_patch(cur["config"], args["config_patch"])
    if not body:
        raise ToolError("Indica name o config_patch")
    res = await ctx.api("PUT", f"{A}/devices/{did}", body=body)
    return {"id": res["id"], "name": res["name"], "config": res["config"], "config_version": res["config_version"]}


register("update_device", "Cambia el nombre o la configuración de un marco. `config_patch` es un JSON Merge Patch sobre "
         "su configuración: por ejemplo {\"photos\":{\"widgets\":[\"time\",\"date\"],\"interval_s\":20},"
         "\"layout\":{\"calendar_mode\":\"week\"}}. El marco lo aplica al momento.",
         obj({"device_id": DEV, "name": S, "config_patch": {"type": "object"}}, ["device_id"]), _update_device,
         idempotent=True)
rest("send_device_command", "Envía una orden a un marco: wake (encender pantalla), sleep, reload (recargar), identify "
     "(mostrar quién es) o update (comprobar e instalar la actualización de la app).", "POST",
     f"{A}/devices/{{device_id}}/command",
     {"device_id": DEV, "type": {"type": "string", "enum": ["wake", "sleep", "reload", "identify", "update"]}},
     ("device_id", "type"))
rest("revoke_device", "Revoca un marco: deja de funcionar y tendrá que emparejarse de nuevo.", "DELETE",
     f"{A}/devices/{{device_id}}", {"device_id": DEV}, ("device_id",), destructive=True)
rest("list_pairing_requests", "Solicitudes de emparejamiento pendientes (cada marco nuevo muestra un código de seis "
     "dígitos en su pantalla).", "GET", f"{A}/pairing")
rest("approve_pairing", "Aprueba un marco nuevo. `code` es el código de seis dígitos que está viendo el marco: así se "
     "demuestra que es el aparato físico y no otro.", "POST", f"{A}/pairing/{{request_id}}/approve",
     {"request_id": S, "code": {"type": "string", "pattern": "^[0-9]{6}$"}, "name": {"type": "string", "maxLength": 80}},
     ("request_id", "code", "name"))
rest("reject_pairing", "Rechaza una solicitud de emparejamiento.", "POST", f"{A}/pairing/{{request_id}}/reject",
     {"request_id": S}, ("request_id",), destructive=True)
rest("get_device_telemetry", "Estado reciente de un marco y muestras del sensor de luz (hasta 600).", "GET",
     f"{A}/devices/{{device_id}}/telemetry", {"device_id": DEV}, ("device_id",))

# ------------------------------------------------------------------ weekly menu
rest("get_menu", "Menú semanal: comidas activas, todas las semanas, cuál es la de hoy y cuál la siguiente.", "GET",
     f"{A}/menu")
rest("set_menu", "Sustituye el menú entero (comidas activas, semanas, semana inicial). Para cambios pequeños usa "
     "set_menu_day o set_menu_week.", "PUT", f"{A}/menu",
     {"meals": {"type": "array", "items": {"type": "string", "enum": MEALS}},
      "weeks": {"type": "array", "maxItems": MAX_MENU_WEEKS, "items": {"type": "object"}},
      "start_week": I, "start_date": S}, idempotent=True)
rest("set_current_menu_week", "Indica qué semana del ciclo es la de ESTA semana; las siguientes siguen el orden y "
     "vuelven a la primera al terminar.", "POST", f"{A}/menu/current-week",
     {"week": {"type": "integer", "minimum": 1, "maximum": MAX_MENU_WEEKS}}, ("week",), idempotent=True)

DAYS = {"lunes": 0, "monday": 0, "martes": 1, "tuesday": 1, "miercoles": 2, "wednesday": 2, "jueves": 3,
        "thursday": 3, "viernes": 4, "friday": 4, "sabado": 5, "saturday": 5, "domingo": 6, "sunday": 6}


def _day_index(value: Any) -> int:
    if isinstance(value, int) and 0 <= value <= 6:
        return value
    plain = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    if plain in DAYS:
        return DAYS[plain]
    raise ToolError("day debe ser 0 (lunes) a 6 (domingo) o un nombre de día")


def _blank_week() -> dict:
    return {"name": "", "days": [{} for _ in range(7)], "shared": {}}


async def _week_edit(ctx: Ctx, week: int, change: Callable[[dict], None]) -> Any:
    menu = (await ctx.api("GET", f"{A}/menu"))["menu"]
    if not 1 <= week <= MAX_MENU_WEEKS or week > len(menu["weeks"]) + 1:
        raise ToolError(f"week debe estar entre 1 y {len(menu['weeks']) + 1} (la siguiente libre crea una semana nueva)")
    if week == len(menu["weeks"]) + 1:
        menu["weeks"].append(_blank_week())
    change(menu["weeks"][week - 1])
    res = await ctx.api("PUT", f"{A}/menu", body=menu)
    return {"week": week, "data": res["menu"]["weeks"][week - 1], "current": res["current"]}


async def _set_day(ctx: Ctx, args: dict) -> Any:
    d = _day_index(args["day"])
    return await _week_edit(ctx, args["week"], lambda w: w["days"][d].update(args["meals"]))


async def _set_week(ctx: Ctx, args: dict) -> Any:
    def change(w: dict) -> None:
        if "name" in args:
            w["name"] = args["name"]
        if "days" in args:
            if len(args["days"]) != 7:
                raise ToolError("days necesita siete elementos, de lunes a domingo")
            w["days"] = args["days"]
        if "shared" in args:
            w["shared"] = args["shared"]
    return await _week_edit(ctx, args["week"], change)


async def _delete_week(ctx: Ctx, args: dict) -> Any:
    menu = (await ctx.api("GET", f"{A}/menu"))["menu"]
    if not 1 <= args["week"] <= len(menu["weeks"]):
        raise ToolError(f"No existe la semana {args['week']}")
    del menu["weeks"][args["week"] - 1]
    res = await ctx.api("PUT", f"{A}/menu", body=menu)
    return {"weeks_left": len(res["menu"]["weeks"]), "current": res["current"]}


MEALS_OBJ = {"type": "object", "properties": MEAL_PROPS, "additionalProperties": False}
register("set_menu_day", "Escribe las comidas de UN día de una semana del menú, sin tocar el resto. `week` empieza en 1 "
         "(la siguiente libre crea la semana); `day` es 0-6 (lunes-domingo) o el nombre del día. `meals` admite "
         "breakfast, midmorning, lunch, snack y dinner; las que no envíes se conservan. Para vaciar una comida envía \"\".",
         obj({"week": {"type": "integer", "minimum": 1, "maximum": MAX_MENU_WEEKS}, "day": {"type": ["integer", "string"]},
              "meals": MEALS_OBJ}, ["week", "day", "meals"]), _set_day, idempotent=True)
register("set_menu_week", "Define una semana del menú entera: nombre opcional, `days` (siete objetos, lunes a domingo, "
         "con breakfast/midmorning/lunch/snack/dinner) y `shared` (comidas iguales toda la semana, p. ej. la fruta de "
         "media mañana). Los campos que no envíes se conservan.",
         obj({"week": {"type": "integer", "minimum": 1, "maximum": MAX_MENU_WEEKS}, "name": S,
              "days": {"type": "array", "minItems": 7, "maxItems": 7, "items": MEALS_OBJ}, "shared": MEALS_OBJ},
             ["week"]), _set_week, idempotent=True)
register("delete_menu_week", "Elimina una semana del ciclo menú.", obj({"week": I}, ["week"]), _delete_week,
         destructive=True)

# ------------------------------------------------------------------ calendars, Home Assistant, secrets
rest("sync_calendar", "Sincroniza un calendario ahora y devuelve cuántos eventos leyó.", "POST",
     f"{A}/calendars/{{source_id}}/sync", {"source_id": S}, ("source_id",))
rest("set_calendar_password", "Guarda (cifrada, solo escritura) la contraseña de un calendario CalDAV. Nunca se vuelve "
     "a mostrar.", "PUT", f"{A}/calendars/{{source_id}}/password",
     {"source_id": S, "password": {"type": "string", "minLength": 1}}, ("source_id", "password"))
rest("set_homeassistant_token", "Guarda (cifrado, solo escritura) el token de acceso de larga duración de Home "
     "Assistant. La URL y las entidades autorizadas están en la configuración (homeassistant).", "PUT",
     f"{A}/homeassistant/token", {"token": {"type": "string", "minLength": 10}}, ("token",))
rest("test_homeassistant", "Prueba la conexión con Home Assistant. Sin argumentos usa la URL y el token guardados.",
     "POST", f"{A}/homeassistant/test",
     {"url": S, "token": S, "verify_tls": {"type": "boolean"}})
rest("list_homeassistant_entities", "Entidades de Home Assistant que se pueden autorizar para los marcos (luces, "
     "interruptores, persianas, cámaras, sensores...). Filtra por `domain`, por ejemplo light.", "GET",
     f"{A}/homeassistant/entities", {"domain": S}, query=("domain",))
rest("list_frigate_cameras", "Cámaras que ve Frigate (con la URL de Frigate de la configuración).", "GET",
     f"{A}/frigate/cameras")

# ------------------------------------------------------------------ photos
rest("list_albums", "Álbumes de fotos y cuántas fotos tiene cada uno.", "GET", f"{A}/albums")
rest("create_album", "Crea un álbum de fotos.", "POST", f"{A}/albums", {"name": {"type": "string", "maxLength": 100}},
     ("name",))
rest("rename_album", "Renombra un álbum.", "PUT", f"{A}/albums/{{album_id}}",
     {"album_id": S, "name": {"type": "string", "maxLength": 100}}, ("album_id", "name"), idempotent=True)
rest("delete_album", "Borra un álbum y todas sus fotos.", "DELETE", f"{A}/albums/{{album_id}}", {"album_id": S},
     ("album_id",), destructive=True)
rest("list_photos", "Fotos de un álbum con su leyenda.", "GET", f"{A}/albums/{{album_id}}/photos", {"album_id": S},
     ("album_id",))
rest("set_photo_caption", "Cambia la leyenda de una foto.", "PATCH", f"{A}/photos/{{photo_id}}",
     {"photo_id": S, "caption": {"type": "string", "maxLength": 200}}, ("photo_id", "caption"), idempotent=True)
rest("delete_photo", "Borra una foto.", "DELETE", f"{A}/photos/{{photo_id}}", {"photo_id": S}, ("photo_id",),
     destructive=True)

# ------------------------------------------------------------------ app updates
rest("list_app_updates", "Versiones de la app de los marcos subidas al servidor, cuál está publicada y el modo de "
     "actualización (off, notify, auto). Subir un APK nuevo se hace desde el panel o con publish.sh.", "GET",
     f"{A}/updates")
rest("publish_app_update", "Publica una versión ya subida para que los marcos la ofrezcan.", "POST",
     f"{A}/updates/{{version_code}}/publish", {"version_code": I}, ("version_code",), idempotent=True)
rest("unpublish_app_update", "Retira la versión publicada: los marcos dejan de ofrecer actualización.", "POST",
     f"{A}/updates/unpublish")
rest("delete_app_update", "Borra una versión no publicada.", "DELETE", f"{A}/updates/{{version_code}}",
     {"version_code": I}, ("version_code",), destructive=True)
rest("set_update_mode", "Modo de actualización de los marcos: off, notify (avisan) o auto (descargan solos).", "PUT",
     f"{A}/updates/settings", {"mode": {"type": "string", "enum": ["off", "notify", "auto"]}}, ("mode",),
     idempotent=True)
