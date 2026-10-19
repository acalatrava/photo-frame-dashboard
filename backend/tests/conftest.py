import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ADMIN_HEADERS = {"X-HomeHQ-Admin": "1"}
ADMIN_PASSWORD = "test-password-12345"


@pytest.fixture()
def data_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setenv("HOMEHQ_DATA_DIR", d)
        monkeypatch.setenv("HOMEHQ_ADMIN_PASSWORD", ADMIN_PASSWORD)
        monkeypatch.setenv("HOMEHQ_LOG_LEVEL", "WARNING")
        yield Path(d)


@pytest.fixture()
def client(data_dir):
    from app import state
    from app.core import db as dbmod
    from app.core.config import get_settings
    from app.api import admin_auth

    get_settings.cache_clear()
    dbmod._engine = None
    from app.api import pairing
    for lim in (admin_auth.login_limiter, pairing.req_limiter, pairing.poll_limiter):
        lim.hits.clear()
    from app.main import create_app

    state.ha.entities.clear()
    state.ha.listeners.clear()
    state.ha.status_listeners.clear()
    state.ha.connected = False
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture()
def admin(client):
    r = client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD},
                    headers=ADMIN_HEADERS)
    assert r.status_code == 200, r.text
    client.headers.update(ADMIN_HEADERS)
    return client


@pytest.fixture()
def paired(admin):
    """(client, device_id, token) with an approved device."""
    r = admin.post("/api/v1/pairing/request", json={"name": "Salón", "model": "PF1007"})
    req = r.json()
    ok = admin.post(f"/api/v1/admin/pairing/{req['request_id']}/approve", json={"code": req["code"], "name": "Salón"})
    assert ok.status_code == 200, ok.text
    poll = admin.post(f"/api/v1/pairing/{req['request_id']}/poll", json={"poll_secret": req["poll_secret"]}).json()
    assert poll["status"] == "approved"
    return admin, poll["device_id"], poll["device_token"]
