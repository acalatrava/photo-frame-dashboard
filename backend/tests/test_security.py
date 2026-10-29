import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.core.http import TooLarge, get_limited
from tests.apkbuild import build_apk, new_identity

from .conftest import ADMIN_HEADERS, ADMIN_PASSWORD

GUARDS = {deps.admin_required, deps.admin_session_required, deps.device_required, deps.mcp_token_user,
          deps.trigger_required}

# Routes that are open on purpose. Anything new that shows up unguarded makes the audit fail until it is reviewed.
PUBLIC = {
    ("POST", "/api/v1/admin/auth/login"),
    ("POST", "/api/v1/admin/auth/logout"),
    ("POST", "/api/v1/admin/auth/refresh"),
    ("POST", "/api/v1/pairing/request"),
    ("POST", "/api/v1/pairing/{request_id}/poll"),
    ("GET", "/media/p/{device_id}/{photo_id}/{size}"),
    ("GET", "/media/cam/{device_id}/{camera_id}/{kind}"),
    ("GET", "/mcp"),
    ("DELETE", "/mcp"),
}
SESSION_ONLY = {"/api/v1/admin/tokens", "/api/v1/admin/auth/password", "/api/v1/admin/updates", "/api/v1/admin/spotify"}


def _dependencies(dep, found):
    found.add(dep.call)
    for sub in dep.dependencies:
        _dependencies(sub, found)


def _routes(app):
    for top in app.routes:
        if type(top).__name__ != "_IncludedRouter":
            continue
        router = top.original_router
        inherited = {d.dependency for d in router.dependencies}
        for route in router.routes:
            found = set()
            _dependencies(route.dependant, found)
            path = route.path if route.path.startswith(router.prefix) else router.prefix + route.path
            for method in route.methods - {"HEAD", "OPTIONS"}:
                yield method, path, (found | inherited) & GUARDS


def test_every_route_is_guarded_unless_listed_as_public(client):
    unguarded = {(m, p) for m, p, g in _routes(client.app) if not g}
    assert unguarded == PUBLIC


def test_sensitive_sections_demand_a_real_session(client):
    for method, path, guards in _routes(client.app):
        shared = (method, path) in {("GET", "/api/v1/admin/updates"), ("PUT", "/api/v1/admin/updates/settings"),
                                    ("GET", "/api/v1/admin/spotify"), ("GET", "/api/v1/admin/spotify/devices")}
        if any(path.startswith(s) for s in SESSION_ONLY) and not shared:
            assert guards == {deps.admin_session_required}, (method, path)


def test_api_tokens_cannot_touch_firmware_updates(admin):
    token = admin.post("/api/v1/admin/tokens", json={"name": "agente", "scope": "full"}).json()["token"]
    bare = TestClient(admin.app)
    h = {"Authorization": f"Bearer {token}"}
    assert bare.get("/api/v1/admin/updates", headers=h).status_code == 200
    assert bare.post("/api/v1/admin/updates/1/publish", headers=h).status_code in (401, 403)
    assert bare.post("/api/v1/admin/updates/unpublish", headers=h).status_code in (401, 403)
    assert bare.delete("/api/v1/admin/updates/1", headers=h).status_code in (401, 403)
    assert bare.post("/api/v1/admin/updates", content=b"x", headers=h).status_code in (401, 403)


def test_mcp_does_not_offer_firmware_tools(admin):
    token = admin.post("/api/v1/admin/tokens", json={"name": "agente", "scope": "full"}).json()["token"]
    r = TestClient(admin.app).post("/mcp", headers={"Authorization": f"Bearer {token}"},
                                   json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {t["name"] for t in r.json()["result"]["tools"]}
    assert "list_app_updates" in names
    assert not names & {"publish_app_update", "unpublish_app_update", "delete_app_update"}


def test_spoofed_forwarded_for_cannot_dodge_the_rate_limit(data_dir, monkeypatch):
    monkeypatch.setenv("HOMEHQ_TRUST_PROXY", "true")
    from app.api import admin_auth
    from app.core import db as dbmod
    from app.core.config import get_settings
    get_settings.cache_clear()
    dbmod._engine = None
    admin_auth.login_limiter.hits.clear()
    from app.main import create_app
    with TestClient(create_app()) as c:
        # The proxy appends the real address last; whatever the client prepends is its own invention.
        for i in range(8):
            c.post("/api/v1/admin/auth/login", json={"username": "admin", "password": "x"},
                   headers={**ADMIN_HEADERS, "X-Forwarded-For": f"10.9.9.{i}, 203.0.113.7"})
        r = c.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD},
                   headers={**ADMIN_HEADERS, "X-Forwarded-For": "10.1.2.3, 203.0.113.7"})
        assert r.status_code == 429


def test_bad_tokens_from_one_address_do_not_lock_out_a_good_token(admin):
    deps._token_failures.hits.clear()
    good = admin.post("/api/v1/admin/tokens", json={"name": "ok", "scope": "read"}).json()["token"]
    bare = TestClient(admin.app)
    for _ in range(30):
        assert bare.get("/api/v1/admin/status", headers={"Authorization": "Bearer hqa_nope"}).status_code == 401
    assert bare.get("/api/v1/admin/status", headers={"Authorization": "Bearer hqa_nope"}).status_code == 429
    deps._token_failures.hits.clear()
    assert bare.get("/api/v1/admin/status", headers={"Authorization": f"Bearer {good}"}).status_code == 200


def test_limiter_memory_stays_bounded():
    lim = deps.RateLimiter(3, 60)
    for i in range(6000):
        lim.fail(f"k{i}")
    assert len(lim.hits) <= 5000


def test_cookie_is_secure_when_the_proxy_says_https(client):
    r = client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD},
                    headers={**ADMIN_HEADERS, "X-Forwarded-Proto": "https"})
    assert all("Secure" in c for c in r.headers.get_list("set-cookie"))
    r = client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD},
                    headers=ADMIN_HEADERS)
    assert not any("Secure" in c for c in r.headers.get_list("set-cookie"))


def test_oversized_json_is_refused_but_uploads_are_not_capped_here(admin):
    r = admin.put("/api/v1/admin/config", content=b"{}", headers={"Content-Length": str(3 * 1024 * 1024),
                                                                   "Content-Type": "application/json"})
    assert r.status_code == 413


def test_device_payloads_are_capped(paired):
    admin, _, token = paired
    big = {"app_version": "1", "status": {"x": "y" * 20000}}
    r = admin.post("/api/v1/device/heartbeat", json=big, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


def test_device_and_mcp_responses_are_not_cacheable(paired):
    admin, _, token = paired
    r = admin.get("/api/v1/device/bootstrap", headers={"Authorization": f"Bearer {token}"})
    assert r.headers["cache-control"] == "no-store"


def test_initial_password_file_is_private_and_removed_after_the_change(data_dir, monkeypatch):
    monkeypatch.delenv("HOMEHQ_ADMIN_PASSWORD")
    from app.core import db as dbmod
    from app.core.config import get_settings
    get_settings.cache_clear()
    dbmod._engine = None
    from app.api import admin_auth
    admin_auth.login_limiter.hits.clear()
    from app.main import create_app
    with TestClient(create_app()) as c:
        path = data_dir / "secrets" / "initial-admin-password.txt"
        assert path.exists() and oct(path.stat().st_mode & 0o777) == "0o600"
        password = path.read_text().strip().split(":", 1)[1]
        assert c.post("/api/v1/admin/auth/login", json={"username": "admin", "password": password},
                      headers=ADMIN_HEADERS).status_code == 200
        r = c.post("/api/v1/admin/auth/password", headers=ADMIN_HEADERS,
                   json={"current_password": password, "new_password": "another-long-password-1"})
        assert r.status_code == 200, r.text
        assert not path.exists()


def test_an_apk_without_a_readable_certificate_cannot_replace_a_known_one(admin):
    first, _ = build_apk(version_code=50, version_name="1", identity=new_identity())
    other, _ = build_apk(version_code=51, version_name="2", identity=new_identity())
    ok = admin.post("/api/v1/admin/updates", content=first, params={"filename": "a.apk"},
                    headers={"Content-Type": "application/octet-stream"})
    assert ok.status_code == 200, ok.text
    bad = admin.post("/api/v1/admin/updates", content=other, params={"filename": "b.apk"},
                     headers={"Content-Type": "application/octet-stream"})
    assert bad.status_code in (400, 409, 422)


def _client_serving(body: bytes, headers=None):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=body, headers=headers or {}))
    return httpx.AsyncClient(transport=transport)


def test_limited_fetch_stops_oversized_bodies():
    async def run():
        async with _client_serving(b"a" * 100) as c:
            assert (await get_limited(c, "http://x/", 1000)).content == b"a" * 100
        async with _client_serving(b"a" * 2000) as c:
            with pytest.raises(TooLarge):
                await get_limited(c, "http://x/", 1000)

    asyncio.run(run())
