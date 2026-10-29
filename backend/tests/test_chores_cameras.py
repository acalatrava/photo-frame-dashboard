import io
from datetime import datetime

import pytest
from PIL import Image

from app.schemas.config import migrate_device
from tests.helpers import connect_ha, set_config, wait_for
from tests.mock_frigate import MockFrigate
from tests.mock_ha import MockServer


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def mock():
    s = MockServer().start()
    yield s
    s.stop()


@pytest.fixture()
def frigate():
    f = MockFrigate().start()
    yield f
    f.stop()


PEOPLE = [{"id": "ana", "name": "Ana", "color": "#2D5BFF"}, {"id": "leo", "name": "Leo", "color": "#E8541E"}]


def test_chores_per_person_weekdays_and_day_reset(paired):
    c, dev, token = paired
    today_wd = datetime.now().weekday()
    other = (today_wd + 3) % 7
    set_config(c, people=PEOPLE, chores=[
        {"id": "basura", "title": "Sacar la basura", "icon": "box", "person_ids": ["ana", "leo"]},
        {"id": "cama", "title": "Hacer la cama", "person_ids": ["leo"], "days": [today_wd]},
        {"id": "otro", "title": "Otro día", "person_ids": ["ana"], "days": [other]},
        {"id": "casa", "title": "Ventilar", "person_ids": []},
    ])
    dash = c.get("/api/v1/device/dashboard", headers=auth(token)).json()["chores"]
    keys = {(i["id"], i["person_id"]) for i in dash["items"]}
    assert keys == {("basura", "ana"), ("basura", "leo"), ("cama", "leo"), ("casa", None)}
    assert not any(i["done"] for i in dash["items"])

    r = c.post("/api/v1/device/chores/done", headers=auth(token),
               json={"ops": [{"chore_id": "basura", "person_id": "leo", "done": True}]})
    assert r.status_code == 200 and r.json()["errors"] == []
    done = {(i["id"], i["person_id"]) for i in r.json()["chores"]["items"] if i["done"]}
    assert done == {("basura", "leo")}  # Ana's check is independent

    # absolute and idempotent: repeating the same op changes nothing, then it can be undone
    c.post("/api/v1/device/chores/done", headers=auth(token),
           json={"ops": [{"chore_id": "basura", "person_id": "leo", "done": True}] * 2})
    r = c.post("/api/v1/device/chores/done", headers=auth(token),
               json={"ops": [{"chore_id": "basura", "person_id": "leo", "done": False}]})
    assert not any(i["done"] for i in r.json()["chores"]["items"])


def test_chores_validation(paired):
    c, dev, token = paired
    set_config(c, people=PEOPLE, chores=[{"id": "a", "title": "A", "person_ids": ["ana"]}])
    h = auth(token)
    bad = c.post("/api/v1/device/chores/done", headers=h, json={"ops": [
        {"chore_id": "a", "person_id": "leo", "done": True},           # not assigned
        {"chore_id": "zzz", "person_id": "", "done": True},            # unknown chore
        {"chore_id": "a", "person_id": "ana", "done": True, "day": "2001-01-01"},  # too old
    ]}).json()
    assert len(bad["errors"]) == 3
    assert not any(i["done"] for i in bad["chores"]["items"])
    cfg = c.get("/api/v1/admin/config").json()["config"]
    cfg["chores"] = [{"id": "x", "title": "X", "days": [9]}]
    assert c.put("/api/v1/admin/config", json=cfg).status_code == 422
    cfg["chores"] = [{"id": "x", "title": "X", "icon": "nope"}]
    assert c.put("/api/v1/admin/config", json=cfg).status_code == 422


def test_cover_controls_and_entity_meta(paired, mock):
    c, dev, token = paired
    connect_ha(c, mock, authorized=("cover.persiana_salon", "scene.cine", "camera.entrada"))
    ents = {e["entity_id"]: e for e in c.get("/api/v1/admin/homeassistant/entities").json()}
    assert ents["cover.persiana_salon"]["controllable"] and "camera.entrada" in ents
    set_config(c, homeassistant={"entity_meta": {"scene.cine": {"name": "Peli", "icon": "film", "color": "#112233"}}})
    dash = c.get("/api/v1/device/dashboard", headers=auth(token)).json()
    assert dash["ha"]["meta"]["scene.cine"] == {"name": "Peli", "icon": "film", "color": "#112233"}
    cover = next(e for e in dash["ha"]["entities"] if e["entity_id"] == "cover.persiana_salon")
    assert cover["attributes"]["current_position"] == 0
    h = auth(token)
    assert c.post("/api/v1/device/ha/service", headers=h, json={
        "entity_id": "cover.persiana_salon", "service": "set_cover_position", "data": {"position": 40}}).status_code == 200
    wait_for(lambda: mock.ha.states["cover.persiana_salon"]["attributes"]["current_position"] == 40)
    assert c.post("/api/v1/device/ha/service", headers=h, json={
        "entity_id": "cover.persiana_salon", "service": "set_cover_position", "data": {"position": 140}}).status_code == 422
    assert c.post("/api/v1/device/ha/service", headers=h, json={
        "entity_id": "cover.persiana_salon", "service": "open_cover"}).status_code == 200
    wait_for(lambda: mock.ha.states["cover.persiana_salon"]["state"] == "open")
    bad = c.get("/api/v1/admin/config").json()["config"]
    bad["homeassistant"]["entity_meta"] = {"scene.cine": {"icon": "nope"}}
    assert c.put("/api/v1/admin/config", json=bad).status_code == 422


def jpeg_ok(data):
    return Image.open(io.BytesIO(data)).format == "JPEG"


def test_frigate_cameras_snapshot_and_signed_stream(paired, frigate):
    c, dev, token = paired
    set_config(c, frigate={"url": frigate.url}, cameras=[
        {"id": "patio", "name": "Patio", "source": "frigate", "frigate_camera": "patio", "fps": 10},
        {"id": "off", "name": "Apagada", "source": "frigate", "frigate_camera": "entrada", "enabled": False},
    ])
    assert c.get("/api/v1/admin/frigate/cameras").json() == ["entrada", "patio"]
    assert jpeg_ok(c.get("/api/v1/admin/cameras/patio/snapshot").content)

    cams = c.get("/api/v1/device/dashboard", headers=auth(token)).json()["cameras"]
    assert [x["id"] for x in cams] == ["patio"]  # disabled cameras are not offered
    snap = c.get(cams[0]["snapshot"])
    assert snap.status_code == 200 and jpeg_ok(snap.content)
    # tampered signature or other camera -> refused
    assert c.get(cams[0]["snapshot"][:-3] + "abc").status_code == 403
    assert c.get(cams[0]["snapshot"].replace("/patio/", "/off/")).status_code == 403

    with c.stream("GET", cams[0]["stream"]) as r:
        assert r.status_code == 200 and r.headers["content-type"].startswith("multipart/x-mixed-replace")
        buf = b""
        for chunk in r.iter_bytes():
            buf += chunk
            if buf.count(b"--homehqframe") >= 3:
                break
    assert buf.count(b"Content-Type: image/jpeg") >= 3


def test_ha_camera_requires_authorisation_and_hides_token(paired, mock):
    c, dev, token = paired
    connect_ha(c, mock, authorized=("camera.entrada",))
    set_config(c, cameras=[{"id": "ent", "name": "Entrada", "source": "ha", "ha_entity": "camera.entrada"}])
    cams = c.get("/api/v1/device/dashboard", headers=auth(token)).json()
    assert jpeg_ok(c.get(cams["cameras"][0]["snapshot"]).content)
    assert "secret-cam-token" not in str(cams)
    set_config(c, homeassistant={"authorized_entities": []})
    assert c.get(cams["cameras"][0]["snapshot"]).status_code == 502  # no longer authorised


def test_camera_failures_are_clean(paired):
    c, dev, token = paired
    set_config(c, frigate={"url": "http://127.0.0.1:1"}, cameras=[
        {"id": "p", "name": "P", "source": "frigate", "frigate_camera": "patio"}])
    cams = c.get("/api/v1/device/dashboard", headers=auth(token)).json()["cameras"]
    assert c.get(cams[0]["stream"]).status_code == 502
    assert c.get("/api/v1/admin/frigate/cameras").status_code == 502
    cfg = c.get("/api/v1/admin/config").json()["config"]
    cfg["cameras"] = [{"id": "z", "name": "Z", "source": "ha", "ha_entity": "light.x"}]
    assert c.put("/api/v1/admin/config", json=cfg).status_code == 422


def test_old_sensor_defaults_are_migrated_but_custom_values_kept():
    old = {"presence": {"min_abs_lux": 8, "min_rel_change": 0.25}}
    assert migrate_device(old)["presence"]["min_abs_lux"] == 2.5
    custom = {"presence": {"min_abs_lux": 8, "min_rel_change": 0.4}}
    assert migrate_device(custom)["presence"]["min_abs_lux"] == 8


def test_week_recurrence_modes():
    from datetime import date, timedelta

    from app.schemas.config import Chore
    from app.services.chores.service import is_due

    def due(c, d):
        return is_due(c, d.isoformat())

    monday = date(2026, 10, 19)  # ISO week 43 (odd)
    assert monday.isocalendar().week == 43
    odd = Chore(id="a", title="A", week_mode="odd")
    even = Chore(id="b", title="B", week_mode="even")
    assert due(odd, monday) and due(odd, monday + timedelta(days=6)) and not due(odd, monday + timedelta(days=7))
    assert not due(even, monday) and due(even, monday + timedelta(days=7))

    every3 = Chore(id="c", title="C", week_mode="every", every_weeks=3, start_date="2026-10-21", days=[5])
    saturday = monday + timedelta(days=5)
    assert due(every3, saturday)                          # week of the start date
    assert not due(every3, saturday + timedelta(days=7))
    assert not due(every3, saturday + timedelta(days=14))
    assert due(every3, saturday + timedelta(days=21))
    assert not due(every3, monday)                        # right week, wrong weekday
    assert due(every3, saturday - timedelta(days=21))     # also counts backwards from the start

    assert due(Chore(id="d", title="D"), monday)          # default: every week, every day


def test_week_recurrence_validation(paired):
    c, dev, token = paired
    cfg = c.get("/api/v1/admin/config").json()["config"]
    cfg["chores"] = [{"id": "x", "title": "X", "week_mode": "every", "every_weeks": 2}]
    assert c.put("/api/v1/admin/config", json=cfg).status_code == 422     # needs a start date
    cfg["chores"] = [{"id": "x", "title": "X", "week_mode": "every", "every_weeks": 1, "start_date": "2026-10-19"}]
    assert c.put("/api/v1/admin/config", json=cfg).status_code == 422     # "every 1 week" is just "all"
    cfg["chores"] = [{"id": "x", "title": "X", "week_mode": "every", "every_weeks": 2, "start_date": "2026-10-19"}]
    assert c.put("/api/v1/admin/config", json=cfg).status_code == 200


def test_nav_order_is_validated_normalised_and_sent_to_frames(paired):
    c, dev, token = paired
    boot = c.get("/api/v1/device/bootstrap", headers=auth(token)).json()["config"]["general"]
    assert boot["nav_order"] == ["calendar", "photos", "chores", "house", "cameras", "shopping", "menu", "music"]
    cfg = c.get("/api/v1/admin/config").json()["config"]
    cfg["general"]["nav_order"] = ["shopping", "house", "house"]
    assert c.put("/api/v1/admin/config", json=cfg).status_code == 200
    boot = c.get("/api/v1/device/bootstrap", headers=auth(token)).json()["config"]["general"]
    assert boot["nav_order"] == ["shopping", "house", "calendar", "photos", "chores", "cameras", "menu", "music"]
    cfg["general"]["nav_order"] = ["settings"]
    assert c.put("/api/v1/admin/config", json=cfg).status_code == 422
