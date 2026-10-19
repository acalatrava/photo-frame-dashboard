import pytest

from tests.helpers import connect_ha, set_config, wait_for
from tests.mock_ha import MockServer, TOKEN


@pytest.fixture()
def mock():
    s = MockServer().start()
    yield s
    s.stop()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_connection_check_and_bad_token(admin, mock):
    ok = admin.post("/api/v1/admin/homeassistant/test", json={"url": mock.url, "token": TOKEN + "x" * 0})
    assert ok.status_code == 200 and ok.json()["version"].startswith("2026")
    bad = admin.post("/api/v1/admin/homeassistant/test", json={"url": mock.url, "token": "wrong-token-123456"})
    assert bad.status_code == 502
    down = admin.post("/api/v1/admin/homeassistant/test", json={"url": "http://127.0.0.1:1", "token": TOKEN})
    assert down.status_code == 502


def test_discovery_states_and_authorization(paired, mock):
    admin, dev, token = paired
    connect_ha(admin, mock)
    ents = admin.get("/api/v1/admin/homeassistant/entities").json()
    ids = {e["entity_id"] for e in ents}
    assert {"light.salon", "sensor.temp_salon", "todo.alexa_shopping_list", "person.ana"} <= ids
    assert "lock.puerta" not in ids  # locks are neither listed nor controllable
    dash = admin.get("/api/v1/device/dashboard", headers=auth(token)).json()
    got = {e["entity_id"]: e for e in dash["ha"]["entities"]}
    assert got["light.salon"]["state"] == "on" and got["light.salon"]["controllable"]
    assert "person.ana" not in got  # not authorised
    assert dash["ha"]["connected"] is True


def test_control_only_authorized_and_whitelisted(paired, mock):
    admin, dev, token = paired
    connect_ha(admin, mock)
    h = auth(token)
    r = admin.post("/api/v1/device/ha/service", headers=h,
                   json={"entity_id": "light.salon", "service": "turn_on", "data": {"brightness_pct": 40}})
    assert r.status_code == 200
    wait_for(lambda: mock.ha.states["light.salon"]["attributes"]["brightness"] == 102)
    # not authorised entity
    assert admin.post("/api/v1/device/ha/service", headers=h,
                      json={"entity_id": "light.otra", "service": "turn_on"}).status_code == 403
    # authorised in config but domain not controllable
    assert admin.post("/api/v1/device/ha/service", headers=h,
                      json={"entity_id": "lock.puerta", "service": "unlock"}).status_code == 403
    # forbidden parameter
    assert admin.post("/api/v1/device/ha/service", headers=h,
                      json={"entity_id": "light.salon", "service": "turn_on", "data": {"rgb_color": [1, 2, 3]}}).status_code == 422
    # forbidden service for domain
    assert admin.post("/api/v1/device/ha/service", headers=h,
                      json={"entity_id": "switch.enchufe", "service": "reload"}).status_code == 403
    assert admin.post("/api/v1/device/ha/service", headers=h,
                      json={"entity_id": "climate.salon", "service": "set_temperature",
                            "data": {"temperature": 99}}).status_code == 422
    assert admin.post("/api/v1/device/ha/service", headers=h,
                      json={"entity_id": "climate.salon", "service": "set_temperature",
                            "data": {"temperature": 22.5}}).status_code == 200
    # unauthenticated device
    assert admin.post("/api/v1/device/ha/service", json={"entity_id": "light.salon", "service": "turn_off"}).status_code == 401


def test_state_changes_stream_to_dashboard(paired, mock):
    admin, dev, token = paired
    connect_ha(admin, mock)
    import httpx
    httpx.post(mock.url + "/_test/set_state", json={"entity_id": "sensor.temp_salon", "state": "23.4"})

    def seen():
        d = admin.get("/api/v1/device/dashboard", headers=auth(token)).json()
        return next(e for e in d["ha"]["entities"] if e["entity_id"] == "sensor.temp_salon")["state"] == "23.4"
    wait_for(seen)


def test_disconnect_keeps_last_state_and_reconnects(paired, mock):
    admin, dev, token = paired
    connect_ha(admin, mock)
    port = mock.port
    mock.stop()
    wait_for(lambda: not admin.get("/health").json()["homeassistant"], timeout=15)
    dash = admin.get("/api/v1/device/dashboard", headers=auth(token)).json()
    assert dash["ha"]["connected"] is False
    assert any(e["entity_id"] == "light.salon" for e in dash["ha"]["entities"])  # last known state kept
    r = admin.post("/api/v1/device/ha/service", headers=auth(token),
                   json={"entity_id": "light.salon", "service": "turn_off"})
    assert r.status_code == 503  # no false "operational" controls
    again = MockServer(port).start()
    try:
        wait_for(lambda: admin.get("/health").json()["homeassistant"], timeout=30)
    finally:
        again.stop()


def test_shopping_via_homeassistant_todo(paired, mock):
    admin, dev, token = paired
    connect_ha(admin, mock)
    ents = admin.get("/api/v1/admin/homeassistant/entities", params={"domain": "todo"}).json()
    assert ents[0]["entity_id"] == "todo.alexa_shopping_list"
    set_config(admin, shopping={"provider": "homeassistant", "ha_entity": "todo.alexa_shopping_list"})
    h = auth(token)
    import httpx
    httpx.post(mock.url + "/_test/todo", json={"summary": "Leche"})  # added "by voice"
    snap = admin.get("/api/v1/device/shopping", headers=h).json()
    assert snap["provider"] == "homeassistant" and [i["name"] for i in snap["items"]] == ["Leche"]
    ops = [
        {"op_id": "op-aaaa01", "type": "add", "name": "Pan", "client_id": "tmp-1"},
        {"op_id": "op-aaaa02", "type": "add", "name": "  leche "},  # duplicate of the voice item
        {"op_id": "op-aaaa03", "type": "set_done", "id": "tmp-1", "done": True},
    ]
    res = admin.post("/api/v1/device/shopping/ops", headers=h, json={"ops": ops}).json()
    names = {i["name"]: i["done"] for i in res["shopping"]["items"]}
    assert names == {"Leche": False, "Pan": True}
    # replaying the same batch is a no-op (no duplicates)
    res2 = admin.post("/api/v1/device/shopping/ops", headers=h, json={"ops": ops}).json()
    assert len(res2["shopping"]["items"]) == 2 and all(r.get("replayed") for r in res2["results"])
    pan = next(i for i in res2["shopping"]["items"] if i["name"] == "Pan")
    rm = admin.post("/api/v1/device/shopping/ops", headers=h,
                    json={"ops": [{"op_id": "op-aaaa04", "type": "remove", "id": pan["id"]}]}).json()
    assert [i["name"] for i in rm["shopping"]["items"]] == ["Leche"]
    # HA goes down: last known list is served, flagged as not ok
    mock.stop()
    wait_for(lambda: not admin.get("/health").json()["homeassistant"], timeout=15)
    snap = admin.get("/api/v1/device/shopping", headers=h).json()
    assert snap["ok"] is False and [i["name"] for i in snap["items"]] == ["Leche"]


def test_ha_token_is_never_exposed(paired, mock):
    admin, dev, token = paired
    connect_ha(admin, mock)
    cfg = admin.get("/api/v1/admin/config").text
    assert TOKEN not in cfg
    boot = admin.get("/api/v1/device/bootstrap", headers=auth(token)).text
    dash = admin.get("/api/v1/device/dashboard", headers=auth(token)).text
    assert TOKEN not in boot and TOKEN not in dash and mock.url not in boot
    import sqlite3
    from app.core.config import get_settings
    raw = sqlite3.connect(get_settings().db_path).execute("select ciphertext from secrets").fetchall()
    assert raw and TOKEN not in raw[0][0]


def test_presence_from_ha(paired, mock):
    admin, dev, token = paired
    connect_ha(admin, mock, authorized=("light.salon",))
    dev_cfg = admin.get(f"/api/v1/admin/devices/{dev}").json()["config"]
    dev_cfg["presence"]["ha_entities"] = ["binary_sensor.pasillo_movimiento"]
    assert admin.put(f"/api/v1/admin/devices/{dev}", json={"config": dev_cfg}).status_code == 200
    import httpx
    httpx.post(mock.url + "/_test/set_state", json={"entity_id": "binary_sensor.pasillo_movimiento", "state": "on"})
    wait_for(lambda: admin.get("/api/v1/device/dashboard", headers=auth(token)).json()["presence"]["ha_active"] is True)
