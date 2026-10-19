"""Home Assistant client: REST for services, WebSocket for real-time state changes.

The backend is the only component holding the HA token. Frames get a filtered view of the
entities that the admin authorised, plus the last known state while HA is unreachable.
"""
import asyncio
import json
import logging
import random
import ssl
import time
from typing import Awaitable, Callable
from urllib.parse import urlparse

import httpx
import websockets

log = logging.getLogger("homehq.ha")

KEEP_ATTRS = (
    "friendly_name", "brightness", "unit_of_measurement", "device_class", "current_temperature",
    "temperature", "hvac_modes", "hvac_action", "hvac_mode", "min_temp", "max_temp", "target_temp_step",
    "current_humidity", "humidity", "supported_color_modes", "color_mode", "icon", "state_class",
    "current_position", "supported_features",
)

ConfigGetter = Callable[[], dict | None]


def slim(state: dict) -> dict:
    attrs = state.get("attributes") or {}
    return {
        "entity_id": state["entity_id"],
        "state": state.get("state"),
        "attributes": {k: attrs[k] for k in KEEP_ATTRS if k in attrs},
        "last_changed": state.get("last_changed"),
    }


class HAError(Exception):
    pass


class HAClient:
    def __init__(self, get_config: ConfigGetter):
        self._get_config = get_config
        self.connected = False
        self.last_error: str | None = None
        self.last_event_ts: float | None = None
        self.last_connected_ts: float | None = None
        self.entities: dict[str, dict] = {}
        self.version: str | None = None
        self._reload = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self.listeners: list[Callable[[list[dict]], Awaitable[None] | None]] = []
        self.status_listeners: list[Callable[[bool], None]] = []

    # ----------------------------------------------------------------- lifecycle
    def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._reload = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="ha-client")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass

    def reload(self) -> None:
        """Called when the HA configuration or token changed. Safe to call from worker threads."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._reload.set)
        else:
            self._reload.set()

    def _set_connected(self, value: bool) -> None:
        if self.connected != value:
            self.connected = value
            for fn in self.status_listeners:
                fn(value)

    # ----------------------------------------------------------------- REST
    @staticmethod
    def _verify(cfg: dict):
        return cfg.get("verify_tls", True)

    async def rest(self, method: str, path: str, json_body=None, cfg: dict | None = None, timeout: float = 10):
        cfg = cfg or self._get_config()
        if not cfg:
            raise HAError("Home Assistant no está configurado")
        headers = {"Authorization": f"Bearer {cfg['token']}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(verify=self._verify(cfg), timeout=timeout) as c:
                r = await c.request(method, cfg["url"] + path, headers=headers, json=json_body)
        except httpx.HTTPError as exc:
            raise HAError(f"No se pudo conectar con Home Assistant: {exc.__class__.__name__}") from exc
        if r.status_code == 401:
            raise HAError("Token de Home Assistant rechazado")
        if r.status_code >= 400:
            raise HAError(f"Home Assistant respondió {r.status_code}")
        return r.json() if r.content else None

    async def rest_bytes(self, path: str, timeout: float = 10) -> tuple[bytes, str]:
        """Raw GET (camera snapshots). Returns the body and its content type."""
        cfg = self._get_config()
        if not cfg:
            raise HAError("Home Assistant no está configurado")
        headers = {"Authorization": f"Bearer {cfg['token']}"}
        try:
            async with httpx.AsyncClient(verify=self._verify(cfg), timeout=timeout) as c:
                r = await c.get(cfg["url"] + path, headers=headers)
        except httpx.HTTPError as exc:
            raise HAError(f"No se pudo conectar con Home Assistant: {exc.__class__.__name__}") from exc
        if r.status_code >= 400:
            raise HAError(f"Home Assistant respondió {r.status_code}")
        return r.content, r.headers.get("content-type", "image/jpeg")

    async def check(self, cfg: dict) -> dict:
        info = await self.rest("GET", "/api/config", cfg=cfg)
        return {"version": info.get("version"), "location_name": info.get("location_name")}

    async def call_service(self, domain: str, service: str, data: dict, return_response: bool = False):
        path = f"/api/services/{domain}/{service}" + ("?return_response" if return_response else "")
        return await self.rest("POST", path, json_body=data, timeout=15)

    async def fetch_states(self) -> list[dict]:
        return await self.rest("GET", "/api/states", timeout=20)

    # ----------------------------------------------------------------- WebSocket loop
    async def _run(self) -> None:
        backoff = 1.0
        while True:
            cfg = self._get_config()
            if not cfg:
                self._set_connected(False)
                self.last_error = None
                self._reload.clear()
                try:
                    await asyncio.wait_for(self._reload.wait(), timeout=30)
                except asyncio.TimeoutError:
                    pass
                continue
            self._reload.clear()
            try:
                await self._session(cfg)
                backoff = 1.0
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - any failure means "reconnect"
                self.last_error = f"{exc.__class__.__name__}: {exc}"[:200]
                log.warning("HA connection lost: %s", self.last_error)
            self._set_connected(False)
            delay = min(60.0, backoff) * (0.7 + random.random() * 0.6)
            backoff = min(60.0, backoff * 2)
            try:
                await asyncio.wait_for(self._reload.wait(), timeout=delay)
                backoff = 1.0
            except asyncio.TimeoutError:
                pass

    async def _session(self, cfg: dict) -> None:
        u = urlparse(cfg["url"])
        scheme = "wss" if u.scheme == "https" else "ws"
        ws_url = f"{scheme}://{u.netloc}{u.path.rstrip('/')}/api/websocket"
        ssl_ctx = None
        if scheme == "wss":
            ssl_ctx = ssl.create_default_context()
            if not cfg.get("verify_tls", True):
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
        async with websockets.connect(ws_url, ssl=ssl_ctx, max_size=16 * 1024 * 1024,
                                      ping_interval=20, ping_timeout=20, open_timeout=10) as ws:
            hello = json.loads(await ws.recv())
            if hello.get("type") != "auth_required":
                raise HAError("Respuesta inesperada de Home Assistant")
            self.version = hello.get("ha_version")
            await ws.send(json.dumps({"type": "auth", "access_token": cfg["token"]}))
            res = json.loads(await ws.recv())
            if res.get("type") != "auth_ok":
                raise HAError("Token de Home Assistant rechazado")
            await ws.send(json.dumps({"id": 1, "type": "get_states"}))
            await ws.send(json.dumps({"id": 2, "type": "subscribe_events", "event_type": "state_changed"}))
            self.last_error = None
            self.last_connected_ts = time.time()
            while True:
                if self._reload.is_set():
                    return
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                msg = json.loads(raw)
                if msg.get("type") == "result" and msg.get("id") == 1:
                    if not msg.get("success"):
                        raise HAError("get_states falló")
                    self.entities = {s["entity_id"]: slim(s) for s in msg["result"]}
                    self._set_connected(True)
                    await self._notify([self.entities[k] for k in self.entities])
                elif msg.get("type") == "event":
                    data = msg["event"]["data"]
                    new = data.get("new_state")
                    eid = data["entity_id"]
                    self.last_event_ts = time.time()
                    if new is None:
                        self.entities.pop(eid, None)
                        continue
                    s = slim(new)
                    self.entities[eid] = s
                    await self._notify([s])

    async def _notify(self, changed: list[dict]) -> None:
        for fn in self.listeners:
            try:
                res = fn(changed)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:  # noqa: BLE001
                log.exception("HA listener failed")
