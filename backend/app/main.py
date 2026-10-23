import asyncio
import logging
import os
import secrets as pysecrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy import text

from . import state
from .api.deps import is_https
from .api import (admin_auth, admin_devices, admin_menu, admin_settings, admin_tokens, admin_updates, device_api, media,
                  pairing)
from .mcp import server as mcp_server
from .core import db as dbmod
from .core import security
from .core.config import APP_VERSION, get_settings
from .core.events import bus
from .core.logging import setup_logging
from .models import AdminUser
from .services import config_service
from .services.calendar import service as cal
from .services.homeassistant import service as has
from .services.weather import service as weather

log = logging.getLogger("homehq")
STATIC = Path(__file__).parent / "static"
MAX_JSON_BODY = 2 * 1024 * 1024


def bootstrap_admin() -> None:
    s = get_settings()
    with dbmod.session_scope() as db:
        if db.query(AdminUser).count():
            return
        password = s.admin_password
        generated = not password
        if generated:
            password = pysecrets.token_urlsafe(12)
        db.add(AdminUser(username=s.admin_user, password_hash=security.hash_password(password),
                         must_change_password=generated))
        if generated:
            # Printed once; the admin is forced to change it at first login.
            log.warning("=" * 60)
            log.warning("Cuenta de administración creada: usuario '%s' contraseña '%s'", s.admin_user, password)
            log.warning("Cámbiala en el primer acceso. No se volverá a mostrar.")
            log.warning("=" * 60)
            path = s.secrets_dir / "initial-admin-password.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.unlink(missing_ok=True)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as fh:
                fh.write(f"{s.admin_user}:{password}\n")


def on_ha_change(changed: list[dict]) -> None:
    """Fan out HA state changes: authorised entities to frames, todo changes to the shopping view."""
    with dbmod.session_scope() as db:
        readable = set(has.readable_entities(db))
        g, _ = config_service.get_global(db)
        todo = g.shopping.ha_entity
        from .models import Device
        presence_by_device = {
            d.id: (d.config or {}).get("presence", {}).get("ha_entities", []) or []
            for d in db.query(Device).filter(Device.status == "active")
        }
    rel = [e for e in changed if e["entity_id"] in readable]
    if not rel:
        return
    if len(changed) > 50:
        rel = [e for e in rel]  # initial snapshot: still only readable entities
    bus.publish("ha.state", {"entities": rel})
    if todo and any(e["entity_id"] == todo for e in rel):
        bus.publish("shopping.changed", {"by": "ha"})
    ids = {e["entity_id"] for e in rel}
    for dev_id, ents in presence_by_device.items():
        if ids & set(ents):
            bus.publish("presence.ha", {"active": any(state.ha.entities.get(x, {}).get("state") == "on"
                                                      for x in ents)}, dev_id)


def on_ha_status(connected: bool) -> None:
    bus.publish("ha.status", {"connected": connected})


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    setup_logging()
    for d in (s.data_dir, s.photos_dir, s.secrets_dir, s.recordings_dir, s.logs_dir, s.updates_dir):
        d.mkdir(parents=True, exist_ok=True)
    if dbmod.engine() is None:
        dbmod.init_engine()
    dbmod.run_migrations()
    bootstrap_admin()
    bus.bind_loop(asyncio.get_running_loop())
    state.ha.listeners.append(on_ha_change)
    state.ha.status_listeners.append(on_ha_status)
    state.ha.start()
    tasks = [asyncio.create_task(cal.scheduler_loop()), asyncio.create_task(weather.scheduler_loop())]
    mdns = None
    if s.mdns_enabled:
        from .integrations.mdns import MdnsAdvertiser
        mdns = MdnsAdvertiser(s.port, s.mdns_hostname)
        await asyncio.to_thread(mdns.start)
    log.info("Home HQ backend %s started", APP_VERSION)
    try:
        yield
    finally:
        for t in tasks:
            t.cancel()
        await state.ha.stop()
        if mdns:
            await asyncio.to_thread(mdns.stop)


def create_app() -> FastAPI:
    app = FastAPI(title="Home HQ", version=APP_VERSION, lifespan=lifespan, docs_url=None, redoc_url=None,
                  openapi_url=None)
    s = get_settings()

    @app.exception_handler(ValidationError)
    async def _validation(_: Request, exc: ValidationError):
        detail = "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors())
        return JSONResponse({"detail": detail}, status_code=422)

    app.add_middleware(CORSMiddleware, allow_origins=s.cors_list, allow_credentials=False,
                       allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                       allow_headers=["Authorization", "Content-Type"], max_age=600)

    @app.middleware("http")
    async def limit_body(request: Request, call_next):
        """JSON endpoints never need big bodies; only the two upload routes may be large."""
        path = request.url.path
        big = path.startswith("/api/v1/admin/albums/") and path.endswith("/photos") or path == "/api/v1/admin/updates"
        if request.method in ("POST", "PUT", "PATCH") and not big:
            declared = request.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > MAX_JSON_BODY:
                return JSONResponse({"detail": "Petición demasiado grande"}, status_code=413)
        return await call_next(request)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        if is_https(request):
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        if request.url.path.startswith(("/admin", "/api/v1/admin")):
            resp.headers.setdefault("X-Frame-Options", "DENY")
            if request.url.path.startswith("/admin"):
                resp.headers.setdefault(
                    "Content-Security-Policy",
                    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
                    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
            resp.headers.setdefault("Cache-Control", "no-store") if request.url.path.startswith("/api") else None
        if request.url.path.startswith(("/mcp", "/api/v1/device")):
            resp.headers.setdefault("Cache-Control", "no-store")
        # Chrome's Private Network Access preflight for LAN backends.
        if request.method == "OPTIONS":
            resp.headers["Access-Control-Allow-Private-Network"] = "true"
        return resp

    @app.get("/health", include_in_schema=False)
    def health():
        try:
            with dbmod.engine().connect() as c:
                c.execute(text("SELECT 1"))
            db_ok = True
        except Exception:  # noqa: BLE001
            db_ok = False
        code = 200 if db_ok else 503
        return JSONResponse({"status": "ok" if db_ok else "error", "version": APP_VERSION, "db": db_ok,
                             "homeassistant": state.ha.connected}, status_code=code)

    for r in (admin_auth.router, admin_devices.router, admin_settings.router, admin_updates.router, admin_menu.router,
              admin_tokens.router, mcp_server.router, device_api.router,
              pairing.router, media.router):
        app.include_router(r)

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/admin/")

    if (STATIC / "admin").exists():
        app.mount("/admin", StaticFiles(directory=STATIC / "admin", html=True), name="admin")
    if s.public_dashboard and (STATIC / "dashboard").exists():
        app.mount("/app", StaticFiles(directory=STATIC / "dashboard", html=True), name="dashboard")
    return app


app = create_app()
