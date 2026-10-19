"""A tiny fake Home Assistant (REST + WebSocket) for tests and demos. NOT a real HA instance.

Run standalone:  python -m tests.mock_ha 8123
"""
import asyncio
import json
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, Response, WebSocket, WebSocketDisconnect

TOKEN = "mock-long-lived-token-0123456789"


def jpeg_bytes(n: int) -> bytes:
    """A small, different JPEG per call (so tests can tell frames apart)."""
    import io

    from PIL import Image

    im = Image.new("RGB", (64, 48), ((n * 40) % 255, 90, 160))
    buf = io.BytesIO()
    im.save(buf, "JPEG")
    return buf.getvalue()


def _now():
    return datetime.now(timezone.utc).isoformat()


class MockHA:
    def __init__(self):
        self.app = FastAPI()
        self.states: dict[str, dict] = {}
        self.todo: dict[str, list[dict]] = {"todo.alexa_shopping_list": []}
        self.calls: list[dict] = []
        self.frames = 0
        self.subs: list[asyncio.Queue] = []
        self._seed()
        self._routes()

    def _seed(self):
        for eid, st, attrs in [
            ("light.salon", "on", {"friendly_name": "Luz salón", "brightness": 180, "supported_color_modes": ["brightness"]}),
            ("light.cocina", "off", {"friendly_name": "Luz cocina"}),
            ("switch.enchufe", "off", {"friendly_name": "Enchufe"}),
            ("climate.salon", "heat", {"friendly_name": "Termostato", "current_temperature": 20.5, "temperature": 21,
                                       "hvac_modes": ["off", "heat"], "min_temp": 7, "max_temp": 30}),
            ("sensor.temp_salon", "20.5", {"friendly_name": "Temperatura salón", "unit_of_measurement": "°C",
                                           "device_class": "temperature"}),
            ("sensor.hum_salon", "44", {"friendly_name": "Humedad salón", "unit_of_measurement": "%",
                                        "device_class": "humidity"}),
            ("binary_sensor.pasillo_movimiento", "off", {"friendly_name": "Movimiento pasillo", "device_class": "motion"}),
            ("scene.cine", "scening", {"friendly_name": "Cine"}),
            ("script.buenas_noches", "off", {"friendly_name": "Buenas noches"}),
            ("lock.puerta", "locked", {"friendly_name": "Puerta"}),
            ("cover.persiana_salon", "closed", {"friendly_name": "Persiana salón", "current_position": 0,
                                                 "supported_features": 15, "device_class": "shutter"}),
            ("camera.entrada", "idle", {"friendly_name": "Entrada", "access_token": "secret-cam-token"}),
            ("person.ana", "home", {"friendly_name": "Ana"}),
            ("todo.alexa_shopping_list", "0", {"friendly_name": "Lista de la compra Alexa"}),
        ]:
            self.states[eid] = {"entity_id": eid, "state": st, "attributes": attrs, "last_changed": _now()}

    def _auth(self, authorization: str | None):
        if authorization != f"Bearer {TOKEN}":
            raise HTTPException(401)

    def set_state(self, eid, state, attrs=None):
        s = self.states.setdefault(eid, {"entity_id": eid, "attributes": {}, "state": state, "last_changed": _now()})
        old = dict(s)
        s["state"] = state
        s["last_changed"] = _now()
        if attrs:
            s["attributes"] = {**s["attributes"], **attrs}
        for q in list(self.subs):
            q.put_nowait({"type": "event", "event": {"event_type": "state_changed",
                          "data": {"entity_id": eid, "old_state": old, "new_state": dict(s)}}})

    def _touch_todo(self, eid):
        self.set_state(eid, str(len([i for i in self.todo[eid] if i["status"] == "needs_action"])))

    def _routes(self):
        app = self.app

        @app.get("/api/config")
        def config(authorization: str | None = Header(None)):
            self._auth(authorization)
            return {"version": "2026.10.2-mock", "location_name": "Casa mock"}

        @app.get("/api/states")
        def states(authorization: str | None = Header(None)):
            self._auth(authorization)
            return list(self.states.values())

        @app.post("/_test/set_state")
        async def test_set(request: Request):
            b = await request.json()
            self.set_state(b["entity_id"], b["state"], b.get("attributes"))
            return {"ok": True}

        @app.post("/_test/todo")
        async def test_todo(request: Request):
            b = await request.json()
            eid = b.get("entity_id", "todo.alexa_shopping_list")
            self.todo[eid].append({"summary": b["summary"], "uid": uuid.uuid4().hex[:8], "status": "needs_action"})
            self._touch_todo(eid)
            return {"ok": True}

        @app.get("/api/camera_proxy/{eid}")
        def camera_proxy(eid: str, authorization: str | None = Header(None)):
            self._auth(authorization)
            if eid not in self.states:
                raise HTTPException(404)
            self.frames += 1
            return Response(jpeg_bytes(self.frames), media_type="image/jpeg")

        @app.get("/_test/calls")
        def calls():
            return self.calls

        @app.post("/api/services/{domain}/{service}")
        async def service(domain: str, service: str, request: Request, authorization: str | None = Header(None)):
            self._auth(authorization)
            data = await request.json() if (await request.body()) else {}
            self.calls.append({"domain": domain, "service": service, "data": data})
            eid = data.get("entity_id")
            if domain == "todo":
                items = self.todo[eid]
                if service == "get_items":
                    return {"changed_states": [], "service_response": {eid: {"items": items}}}
                if service == "add_item":
                    items.append({"summary": data["item"], "uid": uuid.uuid4().hex[:8], "status": "needs_action",
                                  "description": data.get("description")})
                elif service == "update_item":
                    for i in items:
                        if data["item"] in (i["uid"], i["summary"]):
                            if "rename" in data:
                                i["summary"] = data["rename"]
                            if "status" in data:
                                i["status"] = data["status"]
                elif service == "remove_item":
                    refs = data["item"]
                    self.todo[eid] = [i for i in items if i["uid"] not in refs and i["summary"] not in refs]
                self._touch_todo(eid)
                return []
            if domain == "light" and eid in self.states:
                if service == "turn_on":
                    self.set_state(eid, "on", {"brightness": round(data.get("brightness_pct", 100) * 2.55)})
                elif service == "turn_off":
                    self.set_state(eid, "off")
            elif domain == "switch" and eid in self.states:
                self.set_state(eid, "on" if service == "turn_on" else "off")
            elif domain == "cover" and eid in self.states:
                if service == "open_cover":
                    self.set_state(eid, "open", {"current_position": 100})
                elif service == "close_cover":
                    self.set_state(eid, "closed", {"current_position": 0})
                elif service == "set_cover_position":
                    pos = int(data["position"])
                    self.set_state(eid, "open" if pos else "closed", {"current_position": pos})
            elif domain == "climate" and service == "set_temperature":
                self.set_state(eid, self.states[eid]["state"], {"temperature": data["temperature"]})
            return []

        @app.websocket("/api/websocket")
        async def ws(sock: WebSocket):
            await sock.accept()
            await sock.send_json({"type": "auth_required", "ha_version": "2026.10.2-mock"})
            msg = await sock.receive_json()
            if msg.get("access_token") != TOKEN:
                await sock.send_json({"type": "auth_invalid", "message": "bad token"})
                await sock.close()
                return
            await sock.send_json({"type": "auth_ok", "ha_version": "2026.10.2-mock"})
            q: asyncio.Queue = asyncio.Queue()
            self.subs.append(q)

            async def pump():
                while True:
                    await sock.send_json(await q.get())

            task = None
            try:
                task = asyncio.create_task(pump())
                while True:
                    m = await sock.receive_json()
                    if m["type"] == "get_states":
                        await sock.send_json({"id": m["id"], "type": "result", "success": True,
                                              "result": list(self.states.values())})
                    elif m["type"] == "subscribe_events":
                        await sock.send_json({"id": m["id"], "type": "result", "success": True, "result": None})
            except (WebSocketDisconnect, RuntimeError):
                pass
            finally:
                if task:
                    task.cancel()
                if q in self.subs:
                    self.subs.remove(q)


class MockServer:
    def __init__(self, port: int = 0):
        self.ha = MockHA()
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        cfg = uvicorn.Config(self.ha.app, host="127.0.0.1", port=self.port, log_level="warning")
        self.server = uvicorn.Server(cfg)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        while not self.server.started:
            time.sleep(0.05)
        self.port = self.server.servers[0].sockets[0].getsockname()[1]
        return self

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def stop(self):
        self.server.should_exit = True
        self.thread.join(timeout=5)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
    srv = MockServer(port).start()
    print(f"Mock HA on {srv.url} token={TOKEN}")
    while True:
        time.sleep(3600)
