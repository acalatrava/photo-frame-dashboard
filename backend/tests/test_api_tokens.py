from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from .conftest import ADMIN_HEADERS

T = "/api/v1/admin/tokens"


def mint(admin, **body):
    body.setdefault("name", "agente")
    r = admin.post(T, json=body)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture()
def bare(client):
    """Same app, no cookies: what a script holding only a token looks like."""
    return TestClient(client.app)


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_token_is_shown_once_and_never_stored_in_clear(admin):
    t = mint(admin, scope="read")
    assert t["token"].startswith("hqa_") and t["prefix"] == t["token"][:10]
    listed = admin.get(T).json()
    assert listed[0]["id"] == t["id"] and "token" not in listed[0]
    from app.core.db import get_db
    from app.models import ApiToken
    db = next(get_db())
    row = db.get(ApiToken, t["id"])
    assert row.token_hash != t["token"] and t["token"] not in row.token_hash
    db.close()


def test_read_token_reads_but_cannot_write(admin, bare):
    t = mint(admin, scope="read")["token"]
    assert bare.get("/api/v1/admin/config", headers=bearer(t)).status_code == 200
    cfg = admin.get("/api/v1/admin/config").json()["config"]
    r = bare.put("/api/v1/admin/config", json=cfg, headers=bearer(t))
    assert r.status_code == 403


def test_full_token_writes_without_csrf_header_or_cookie(admin, bare):
    t = mint(admin, scope="full")["token"]
    cfg = bare.get("/api/v1/admin/config", headers=bearer(t)).json()["config"]
    cfg["general"]["language"] = "en"
    assert bare.put("/api/v1/admin/config", json=cfg, headers=bearer(t)).status_code == 200
    assert admin.get("/api/v1/admin/config").json()["config"]["general"]["language"] == "en"


def test_token_cannot_mint_tokens_or_change_password(admin, bare):
    t = mint(admin, scope="full")["token"]
    assert bare.post(T, json={"name": "otro", "scope": "full"}, headers=bearer(t)).status_code in (401, 403)
    assert bare.get(T, headers=bearer(t)).status_code == 401
    pw = {"current_password": "test-password-12345", "new_password": "y" * 16}
    assert bare.post("/api/v1/admin/auth/password", json=pw, headers=bearer(t)).status_code in (401, 403)
    assert bare.post("/api/v1/admin/auth/password", json=pw, headers={**bearer(t), **ADMIN_HEADERS}).status_code == 401


def test_revoked_expired_and_garbage_tokens_are_rejected(admin, bare):
    t = mint(admin, scope="read")
    assert bare.get("/api/v1/admin/config", headers=bearer(t["token"])).status_code == 200
    assert admin.delete(f"{T}/{t['id']}").status_code == 200
    r = bare.get("/api/v1/admin/config", headers=bearer(t["token"]))
    assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"

    e = mint(admin, scope="read", expires_days=1)
    from app.core.db import get_db
    from app.models import ApiToken
    db = next(get_db())
    db.get(ApiToken, e["id"]).expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    db.close()
    assert bare.get("/api/v1/admin/config", headers=bearer(e["token"])).status_code == 401
    assert bare.get("/api/v1/admin/config", headers=bearer("hqa_nope")).status_code == 401
    assert bare.get("/api/v1/admin/config", headers=bearer("not-even-prefixed")).status_code == 401


def test_a_device_token_is_not_an_admin_token(paired, bare):
    _, _, device_token = paired
    assert bare.get("/api/v1/admin/config", headers=bearer(device_token)).status_code == 401


def test_repeated_bad_tokens_get_rate_limited(client):
    from app.api import deps
    deps._token_failures.hits.clear()
    for _ in range(30):
        assert client.get("/api/v1/admin/config", headers=bearer("hqa_bad")).status_code == 401
    assert client.get("/api/v1/admin/config", headers=bearer("hqa_bad")).status_code == 429
    deps._token_failures.hits.clear()


def test_tokens_are_per_user_and_capped(admin):
    for i in range(20):
        mint(admin, name=f"t{i}")
    assert admin.post(T, json={"name": "uno más"}).status_code == 400
    assert admin.delete(f"{T}/99999").status_code == 404


def test_cookie_flow_still_needs_the_csrf_header(admin):
    cfg = admin.get("/api/v1/admin/config").json()["config"]
    r = admin.put("/api/v1/admin/config", json=cfg, headers={"X-HomeHQ-Admin": "0"})
    assert r.status_code == 403
