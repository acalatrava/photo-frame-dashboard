from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.events import bus
from tests.helpers import set_config

PEOPLE = [{"id": "ana", "name": "Ana", "color": "#2D5BFF"}]
T = "/api/v1/admin/tokens"


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def mint(admin, scope):
    r = admin.post(T, json={"name": f"t-{scope}", "scope": scope})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture()
def bare(client):
    return TestClient(client.app)


def last_command():
    return [m for m in bus.recent if m["topic"] == "device.command"][-1]


# ------------------------------------------------------------------ triggers
def test_trigger_token_can_fire_but_not_administer(paired, bare):
    c, dev, _ = paired
    token = mint(c, "trigger")
    r = bare.post("/api/v1/trigger", headers=auth(token),
                  json={"action": "show_view", "view": "cameras", "camera": "puerta", "duration_s": 20})
    assert r.status_code == 200, r.text
    assert r.json()["offline"] == [dev] and r.json()["sent"] == []
    msg = last_command()
    assert msg["device_id"] == dev
    assert msg["data"]["type"] == "trigger" and msg["data"]["camera"] == "puerta" and msg["data"]["duration_s"] == 20
    for method, path in (("GET", "/api/v1/admin/config"), ("GET", "/api/v1/admin/devices"), ("POST", "/mcp")):
        assert bare.request(method, path, headers=auth(token)).status_code in (401, 403), path
    assert bare.post(T, json={"name": "x", "scope": "full"}, headers=auth(token)).status_code in (401, 403)


def test_read_token_cannot_trigger_and_full_token_can(paired, bare):
    c, dev, _ = paired
    body = {"action": "wake"}
    assert bare.post("/api/v1/trigger", json=body, headers=auth(mint(c, "read"))).status_code == 403
    assert bare.post("/api/v1/trigger", json=body).status_code == 401
    assert bare.post("/api/v1/trigger", json=body, headers=auth(mint(c, "full"))).status_code == 200


def test_trigger_targets_by_name_and_validates(paired, bare):
    c, dev, _ = paired
    h = auth(mint(c, "trigger"))
    assert bare.post("/api/v1/trigger", headers=h, json={"action": "wake", "device": "salón"}).status_code == 200
    assert bare.post("/api/v1/trigger", headers=h, json={"action": "wake", "device": "garaje"}).status_code == 404
    assert bare.post("/api/v1/trigger", headers=h, json={"action": "show_view", "view": "../x"}).status_code == 422
    assert bare.post("/api/v1/trigger", headers=h, json={"action": "alert", "sound": "none"}).status_code == 422
    assert bare.post("/api/v1/trigger", headers=h, json={"action": "alert", "message": "x" * 300}).status_code == 422
    assert bare.post("/api/v1/trigger", headers=h, json={"action": "reboot"}).status_code == 422
    ok = bare.post("/api/v1/trigger", headers=h, json={"action": "alert", "message": "Llaman a la puerta", "speak": True})
    assert ok.status_code == 200
    assert last_command()["data"]["message"] == "Llaman a la puerta"


def test_panel_can_try_an_alert_on_one_frame(paired):
    c, dev, _ = paired
    r = c.post(f"/api/v1/admin/devices/{dev}/trigger", json={"action": "alert", "message": "Prueba", "device": "otro"})
    assert r.status_code == 200
    assert last_command()["device_id"] == dev
    assert c.post("/api/v1/admin/devices/nope/trigger", json={"action": "wake"}).status_code == 404


# ------------------------------------------------------------------ alarms
def alarm(**kw):
    return {"id": "cole", "name": "Colegio", "time": "07:30", "days": [0, 1, 2, 3, 4], "message": "A vestirse", **kw}


def test_alarms_reach_only_their_frames(paired):
    c, dev, token = paired
    set_config(c, alarms=[alarm(), alarm(id="otra", device_ids=["otro-marco"]), alarm(id="off", enabled=False)])
    cfg = c.get("/api/v1/device/bootstrap", headers=auth(token)).json()["config"]
    assert [a["id"] for a in cfg["alarms"]] == ["cole"]
    set_config(c, alarms=[alarm(device_ids=[dev])])
    cfg = c.get("/api/v1/device/bootstrap", headers=auth(token)).json()["config"]
    assert [a["id"] for a in cfg["alarms"]] == ["cole"]


def test_alarm_validation(admin):
    cfg = admin.get("/api/v1/admin/config").json()["config"]
    for bad in (alarm(time="25:00"), alarm(days=[7]), alarm(sound="none", message=""), alarm(volume=0),
                alarm(duration_s=1), alarm(id="Mal Id")):
        cfg["alarms"] = [bad]
        assert admin.put("/api/v1/admin/config", json=cfg).status_code == 422, bad
    cfg["alarms"] = [alarm(), alarm()]
    assert admin.put("/api/v1/admin/config", json=cfg).status_code == 422


def test_sound_defaults_and_validation(admin):
    cfg = admin.get("/api/v1/admin/devices").json()
    assert isinstance(cfg, list)
    from app.schemas.config import DeviceConfig
    d = DeviceConfig()
    assert d.presence.sleep_on_lights_off is True and d.presence.lights_off_lux == 10
    assert d.sounds.chime.enabled is False and d.sounds.chime.quiet is True
    assert d.photos.transition == "fade" and d.photos.text_color == "#FFFFFF"
    for bad in ({"sounds": {"volume": 101}}, {"sounds": {"chime": {"quiet_start": "99:00"}}},
                {"photos": {"text_color": "red"}}, {"display": {"night_color": "#12"}},
                {"presence": {"lights_off_lux": 0}}):
        with pytest.raises(Exception):
            DeviceConfig.model_validate(bad)


# ------------------------------------------------------------------ one-off chores
def test_one_off_chore_stays_until_done_then_disappears(paired):
    c, dev, token = paired
    today = date.today()
    set_config(c, people=PEOPLE, chores=[
        {"id": "itv", "title": "Llevar el coche a la ITV", "person_ids": ["ana"], "week_mode": "once",
         "start_date": (today - timedelta(days=2)).isoformat()},
        {"id": "futura", "title": "Futura", "person_ids": ["ana"], "week_mode": "once",
         "start_date": (today + timedelta(days=2)).isoformat()},
    ])
    h = auth(token)
    items = c.get("/api/v1/device/dashboard", headers=h).json()["chores"]["items"]
    assert [i["id"] for i in items] == ["itv"]
    assert items[0]["once"] is True and items[0]["overdue"] is True and items[0]["done"] is False
    r = c.post("/api/v1/device/chores/done", headers=h,
               json={"ops": [{"chore_id": "itv", "person_id": "ana", "done": True}]}).json()
    assert r["errors"] == [] and r["chores"]["items"][0]["done"] is True
    assert r["chores"]["items"][0]["overdue"] is False


def test_one_off_chore_needs_a_day(admin):
    cfg = admin.get("/api/v1/admin/config").json()["config"]
    cfg["chores"] = [{"id": "x", "title": "X", "week_mode": "once"}]
    assert admin.put("/api/v1/admin/config", json=cfg).status_code == 422
