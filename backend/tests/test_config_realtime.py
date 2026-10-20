import json
import threading
import time

from tests.helpers import set_config, wait_for


def h(t): return {"Authorization": f"Bearer {t}"}


def test_default_config_is_spanish(paired):
    c, dev, token = paired
    cfg = c.get("/api/v1/device/bootstrap", headers=h(token)).json()["config"]
    assert cfg["general"]["language"] == "es-ES" and cfg["general"]["timezone"] == "Europe/Madrid"


def test_config_validation(admin):
    cfg = admin.get("/api/v1/admin/config").json()["config"]
    for mutate in (
        lambda c: c["general"].update(timezone="Mars/Olympus"),
        lambda c: c["general"].update(language="fr"),
        lambda c: c.update(unknown_field=1),
        lambda c: c["shopping"].update(provider="homeassistant", ha_entity="light.nope"),
        lambda c: c["homeassistant"].update(url="javascript:alert(1)"),
    ):
        bad = json.loads(json.dumps(cfg))
        mutate(bad)
        r = admin.put("/api/v1/admin/config", json=bad)
        assert r.status_code in (400, 422), r.text
    assert admin.get("/api/v1/admin/config").json()["config"] == cfg


def test_device_config_override_and_version_bump(paired):
    c, dev, token = paired
    v1 = c.get("/api/v1/device/bootstrap", headers=h(token)).json()["config"]["version"]
    cfg = c.get(f"/api/v1/admin/devices/{dev}").json()["config"]
    cfg["presence"]["sensitivity"] = "high"
    cfg["display"]["night_brightness"] = 5
    r = c.put(f"/api/v1/admin/devices/{dev}", json={"config": cfg})
    assert r.status_code == 200, r.text
    b = c.get("/api/v1/device/bootstrap", headers=h(token)).json()["config"]
    assert b["version"] != v1 and b["device_config"]["presence"]["sensitivity"] == "high"
    cfg["presence"]["sensitivity"] = "ultra"
    assert c.put(f"/api/v1/admin/devices/{dev}", json={"config": cfg}).status_code in (400, 422)


def test_sse_receives_config_and_commands(paired):
    c, dev, token = paired
    got = []

    def listen():
        with c.stream("GET", "/api/v1/device/events", headers=h(token)) as r:
            assert r.status_code == 200
            for line in r.iter_lines():
                if line.startswith("event:"):
                    got.append(line[6:].strip())
                if len(got) >= 3:
                    break

    t = threading.Thread(target=listen, daemon=True)
    t.start()
    time.sleep(0.8)
    set_config(c, general={"language": "en"})
    c.post(f"/api/v1/admin/devices/{dev}/command", json={"type": "wake"})
    t.join(timeout=10)
    assert "config.changed" in got and "device.command" in got


def test_sse_requires_token(client):
    assert client.get("/api/v1/device/events").status_code == 401


def test_telemetry_and_recording(paired):
    c, dev, token = paired
    assert c.post(f"/api/v1/admin/devices/{dev}/recording", json={"action": "start", "name": "pasillo"}).status_code == 200
    now = time.time()
    samples = [[now + i, 100 + i, 0] for i in range(5)]
    r = c.post("/api/v1/device/telemetry", headers=h(token), json={"samples": samples})
    assert r.status_code == 200
    assert c.post("/api/v1/device/telemetry", headers=h(token), json={"samples": [[1]]}).status_code == 422
    c.post(f"/api/v1/admin/devices/{dev}/recording", json={"action": "stop"})
    recs = c.get("/api/v1/admin/recordings").json()
    assert recs
    csv = c.get(f"/api/v1/admin/recordings/{recs[0]['id']}/csv")
    assert csv.status_code == 200 and len(csv.text.strip().splitlines()) >= 5
    tel = c.get(f"/api/v1/admin/devices/{dev}/telemetry").json()
    assert tel


def test_status_endpoint(admin):
    s = admin.get("/api/v1/admin/status").json()
    assert s["version"] and "homeassistant" in s


def test_photo_widgets_and_calendar_mode_reach_the_frame(paired):
    c, dev, token = paired
    cfg = c.get(f"/api/v1/admin/devices/{dev}").json()["config"]
    assert cfg["photos"]["widgets"] == ["time", "date", "weather", "calendar", "people"]
    assert cfg["layout"]["calendar_mode"] == "day"
    cfg["photos"]["widgets"] = ["tasks", "time", "time"]
    cfg["layout"]["calendar_mode"] = "week"
    assert c.put(f"/api/v1/admin/devices/{dev}", json={"config": cfg}).status_code == 200
    got = c.get("/api/v1/device/bootstrap", headers=h(token)).json()["config"]["device_config"]
    assert got["photos"]["widgets"] == ["time", "tasks"]
    assert got["layout"]["calendar_mode"] == "week"
    cfg["photos"]["widgets"] = []
    assert c.put(f"/api/v1/admin/devices/{dev}", json={"config": cfg}).status_code == 200
    cfg["photos"]["widgets"] = ["clock"]
    assert c.put(f"/api/v1/admin/devices/{dev}", json={"config": cfg}).status_code in (400, 422)
    cfg["photos"]["widgets"] = []
    cfg["layout"]["calendar_mode"] = "year"
    assert c.put(f"/api/v1/admin/devices/{dev}", json={"config": cfg}).status_code in (400, 422)
