from urllib.parse import parse_qs, urlparse

import pytest

from app.services.spotify import service as sp
from tests.helpers import set_config
from tests.mock_spotify import MockSpotify


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def spotify(monkeypatch):
    m = MockSpotify().start()
    monkeypatch.setattr(sp, "ACCOUNTS", m.url)
    monkeypatch.setattr(sp, "API", m.url + "/v1")
    sp._access.update(token="", exp=0.0)
    sp._pending.clear()
    yield m
    m.stop()


def link(c, m):
    set_config(c, spotify={"enabled": True, "client_id": "abc123"})
    url = c.post("/api/v1/admin/spotify/authorize").json()["url"]
    q = parse_qs(urlparse(url).query)
    assert q["code_challenge_method"] == ["S256"] and q["client_id"] == ["abc123"]
    m.challenge = q["code_challenge"][0]
    return q["state"][0]


def test_connect_with_pasted_redirect_then_frame_controls(paired, spotify):
    c, dev, token = paired
    h = auth(token)
    assert c.get("/api/v1/device/music/state", headers=h).status_code == 409
    state = link(c, spotify)
    r = c.post("/api/v1/admin/spotify/connect", json={"code": f"http://127.0.0.1:8787/callback?code=goodcode&state={state}"})
    assert r.status_code == 200 and c.get("/api/v1/admin/spotify").json()["connected"] is True
    assert c.get("/api/v1/device/dashboard", headers=h).json()["music"] == {"configured": True}

    s = c.get("/api/v1/device/music/state", headers=h).json()
    assert s["playing"] and s["track"]["name"] == "Canción" and s["track"]["art"] == "https://i.scdn.co/image/x"
    assert s["device"]["name"] == "Echo cocina"
    assert c.get("/api/v1/device/music/devices", headers=h).json()[0]["name"] == "Echo cocina"
    assert [p["name"] for p in c.get("/api/v1/device/music/playlists", headers=h).json()] == ["Cocina"]
    assert c.get("/api/v1/device/music/search?q=hola", headers=h).json()[0]["kind"] == "track"

    spotify.calls.clear()
    dev_id = "a" * 20
    ok = c.post("/api/v1/device/music/control", headers=h, json={"action": "play", "uri": "spotify:playlist:" + "c" * 22, "device_id": dev_id})
    assert ok.status_code == 200
    put = [x for x in spotify.calls if x[0] == "PUT"][0]
    assert put[1] == "/v1/me/player/play" and put[2] == {"device_id": dev_id} and "context_uri" in put[3]
    assert put[4].startswith("Bearer AT")
    c.post("/api/v1/device/music/control", headers=h, json={"action": "volume", "volume": 40})
    assert any(x[1] == "/v1/me/player/volume" and x[2]["volume_percent"] == "40" for x in spotify.calls if x[0] == "PUT")


def test_bad_code_and_validation(paired, spotify):
    c, dev, token = paired
    h = auth(token)
    link(c, spotify)
    assert c.post("/api/v1/admin/spotify/connect", json={"code": "wrongcode"}).status_code == 400
    assert c.post("/api/v1/admin/spotify/connect", json={"code": "goodcode"}).status_code == 400  # verifier already used
    state = link(c, spotify)
    assert c.post("/api/v1/admin/spotify/connect", json={"code": f"?code=goodcode&state=otro"}).status_code == 400
    assert c.post("/api/v1/admin/spotify/connect", json={"code": f"?code=goodcode&state={state}"}).status_code == 200
    for body in ({"action": "explode"}, {"action": "play", "uri": "https://evil"}, {"action": "play", "device_id": "x y"},
                 {"action": "volume", "volume": 300}):
        assert c.post("/api/v1/device/music/control", headers=h, json=body).status_code in (422,), body
    cfg = c.get("/api/v1/admin/config").json()["config"]
    cfg["spotify"]["redirect_uri"] = "http://192.168.1.5:8787/callback"
    assert c.put("/api/v1/admin/config", json=cfg).status_code == 422


def test_revoked_refresh_token_disconnects(paired, spotify):
    c, dev, token = paired
    state = link(c, spotify)
    c.post("/api/v1/admin/spotify/connect", json={"code": f"?code=goodcode&state={state}"})
    sp._access.update(token="", exp=0.0)
    spotify.revoked = True
    r = c.get("/api/v1/device/music/state", headers=auth(token))
    assert r.status_code == 409
    assert c.get("/api/v1/admin/spotify").json()["connected"] is False


def test_disconnect_forgets_the_account(paired, spotify):
    c, dev, token = paired
    state = link(c, spotify)
    c.post("/api/v1/admin/spotify/connect", json={"code": f"?code=goodcode&state={state}"})
    assert c.delete("/api/v1/admin/spotify").json() == {"connected": False}
    assert c.get("/api/v1/device/music/state", headers=auth(token)).status_code == 409


def test_account_link_needs_a_real_session(client, paired):
    c, dev, token = paired
    from fastapi.testclient import TestClient
    t = c.post("/api/v1/admin/tokens", json={"name": "x", "scope": "full"}).json()["token"]
    bare = TestClient(client.app)
    h = auth(t)
    assert bare.get("/api/v1/admin/spotify", headers=h).status_code == 200
    for method, path in (("POST", "/api/v1/admin/spotify/authorize"), ("POST", "/api/v1/admin/spotify/connect"), ("DELETE", "/api/v1/admin/spotify")):
        assert bare.request(method, path, headers=h, json={"code": "abcdefgh"}).status_code in (401, 403), path
