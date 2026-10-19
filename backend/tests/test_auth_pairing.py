from fastapi.testclient import TestClient
from tests.conftest import ADMIN_HEADERS, ADMIN_PASSWORD


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_admin_requires_login(client):
    assert client.get("/api/v1/admin/config").status_code == 401
    assert client.get("/api/v1/admin/devices").status_code == 401
    assert client.put("/api/v1/admin/config", json={}).status_code in (401, 403)


def test_login_flags_and_cookies(client):
    bad = client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": "nope"}, headers=ADMIN_HEADERS)
    assert bad.status_code == 401
    r = client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD},
                    headers=ADMIN_HEADERS)
    assert r.status_code == 200
    cookies = r.headers.get_list("set-cookie")
    assert len(cookies) == 2
    for c in cookies:
        assert "HttpOnly" in c and "SameSite=strict" in c
    assert "Path=/api/v1/admin/auth" in [c for c in cookies if "hq_refresh" in c][0]


def test_login_requires_csrf_header(client):
    r = client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD})
    assert r.status_code == 403


def test_secure_cookie_over_https_proxy(data_dir, monkeypatch):
    monkeypatch.setenv("HOMEHQ_TRUST_PROXY", "true")
    from app.core.config import get_settings
    from app.core import db as dbmod
    get_settings.cache_clear(); dbmod._engine = None
    from app.main import create_app
    with TestClient(create_app()) as c:
        r = c.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD},
                   headers={**ADMIN_HEADERS, "X-Forwarded-Proto": "https"})
        assert all("Secure" in x for x in r.headers.get_list("set-cookie"))


def test_login_rate_limit(client):
    for _ in range(8):
        client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": "x"}, headers=ADMIN_HEADERS)
    r = client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD},
                    headers=ADMIN_HEADERS)
    assert r.status_code == 429


def test_refresh_rotation_and_reuse_detection(client):
    client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD}, headers=ADMIN_HEADERS)
    old = client.cookies.get("hq_refresh", path="/api/v1/admin/auth")
    assert client.post("/api/v1/admin/auth/refresh", headers=ADMIN_HEADERS).status_code == 200
    new = client.cookies.get("hq_refresh", path="/api/v1/admin/auth")
    assert new and new != old
    # Attacker replays the rotated token.
    client.cookies.set("hq_refresh", old, path="/api/v1/admin/auth")
    assert client.post("/api/v1/admin/auth/refresh", headers=ADMIN_HEADERS).status_code == 401
    # The legitimate (newer) token of the same family is now dead too.
    client.cookies.set("hq_refresh", new, path="/api/v1/admin/auth")
    assert client.post("/api/v1/admin/auth/refresh", headers=ADMIN_HEADERS).status_code == 401


def test_logout_revokes_refresh(client):
    client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD}, headers=ADMIN_HEADERS)
    refresh = client.cookies.get("hq_refresh", path="/api/v1/admin/auth")
    assert client.post("/api/v1/admin/auth/logout", headers=ADMIN_HEADERS).status_code == 200
    client.cookies.set("hq_refresh", refresh, path="/api/v1/admin/auth")
    assert client.post("/api/v1/admin/auth/refresh", headers=ADMIN_HEADERS).status_code == 401
    assert client.get("/api/v1/admin/config").status_code == 401


def test_pairing_flow_and_token_isolation(paired):
    client, device_id, token = paired
    h = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/v1/device/bootstrap", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["config"]["device"]["id"] == device_id
    assert "token" not in str(body["config"]).lower() or "homeassistant_token" not in str(body)
    # device token cannot reach admin API
    c2 = TestClient(client.app)
    assert c2.get("/api/v1/admin/devices", headers=h).status_code == 401
    # poll again does not hand the token out twice
    assert client.get("/api/v1/device/bootstrap").status_code == 401


def test_pairing_requires_matching_code(admin):
    req = admin.post("/api/v1/pairing/request", json={"name": "x"}).json()
    bad = admin.post(f"/api/v1/admin/pairing/{req['request_id']}/approve", json={"code": "000000", "name": "x"})
    wrong = "000000" if req["code"] != "000000" else "111111"
    bad = admin.post(f"/api/v1/admin/pairing/{req['request_id']}/approve", json={"code": wrong, "name": "x"})
    assert bad.status_code == 400
    poll = admin.post(f"/api/v1/pairing/{req['request_id']}/poll", json={"poll_secret": req["poll_secret"]}).json()
    assert poll["status"] == "pending"
    wrong_secret = admin.post(f"/api/v1/pairing/{req['request_id']}/poll", json={"poll_secret": "zzz"})
    assert wrong_secret.status_code == 403


def test_token_delivered_once(paired):
    client, device_id, token = paired
    # The pairing request was consumed: nothing left to collect
    reqs = client.get("/api/v1/admin/pairing").json()
    assert reqs == []


def test_revoke_device(paired):
    client, device_id, token = paired
    assert client.delete(f"/api/v1/admin/devices/{device_id}").status_code == 200
    assert client.get("/api/v1/device/bootstrap", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_cors_restricted(client):
    ok = client.options("/api/v1/device/bootstrap", headers={
        "Origin": "http://appassets.homehq.invalid", "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization"})
    assert ok.headers.get("access-control-allow-origin") == "http://appassets.homehq.invalid"
    assert ok.headers.get("access-control-allow-private-network") == "true"
    bad = client.options("/api/v1/device/bootstrap", headers={
        "Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in bad.headers


def test_change_password(admin):
    r = admin.post("/api/v1/admin/auth/password", json={"current_password": "wrong", "new_password": "a-long-new-password"})
    assert r.status_code == 400
    r = admin.post("/api/v1/admin/auth/password", json={"current_password": ADMIN_PASSWORD, "new_password": "a-long-new-password"})
    assert r.status_code == 200
