import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def bare(client):
    return TestClient(client.app)


def mint(admin, scope):
    return admin.post("/api/v1/admin/tokens", json={"name": "agente", "scope": scope}).json()["token"]


def rpc(client, token, method, params=None, rid=1, headers=None):
    h = {"Authorization": f"Bearer {token}", **(headers or {})}
    return client.post("/mcp", json={"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}, headers=h)


def call(client, token, tool, /, **args):
    r = rpc(client, token, "tools/call", {"name": tool, "arguments": args})
    assert r.status_code == 200, r.text
    res = r.json()["result"]
    text = res["content"][0]["text"]
    return res["isError"], (json.loads(text) if not res["isError"] else text)


def test_requires_a_bearer_token_and_ignores_cookies(admin, bare):
    r = bare.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
    assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"
    assert admin.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}).status_code == 401
    assert rpc(bare, "hqa_wrong", "ping").status_code == 401


def test_handshake_and_tool_listing_follow_the_token_scope(admin, bare):
    full, read = mint(admin, "full"), mint(admin, "read")
    init = rpc(bare, full, "initialize", {"protocolVersion": "2025-06-18"}).json()["result"]
    assert init["protocolVersion"] == "2025-06-18" and "tools" in init["capabilities"]
    assert rpc(bare, full, "initialize", {"protocolVersion": "1999-01-01"}).json()["result"]["protocolVersion"] \
        == "2025-06-18"
    names_full = {t["name"] for t in rpc(bare, full, "tools/list").json()["result"]["tools"]}
    names_read = {t["name"] for t in rpc(bare, read, "tools/list").json()["result"]["tools"]}
    assert {"update_config", "set_menu_day", "get_config"} <= names_full
    assert "get_config" in names_read and "update_config" not in names_read and names_read < names_full
    for t in rpc(bare, full, "tools/list").json()["result"]["tools"]:
        assert t["inputSchema"]["type"] == "object" and t["description"] and "readOnlyHint" in t["annotations"]


def test_notifications_get_202_and_unknown_methods_error(admin, bare):
    t = mint(admin, "read")
    r = bare.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                  headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 202 and r.content == b""
    assert rpc(bare, t, "nope").json()["error"]["code"] == -32601
    assert bare.post("/mcp", content=b"{", headers={"Authorization": f"Bearer {t}"}).status_code == 400
    assert bare.get("/mcp").status_code == 405


def test_read_token_can_read_but_a_write_tool_is_refused(admin, bare):
    t = mint(admin, "read")
    err, cfg = call(bare, t, "get_config")
    assert not err and cfg["config"]["general"]["language"]
    err, text = call(bare, t, "update_config", patch={"general": {"language": "en"}})
    assert err and "solo lectura" in text


def test_update_config_merges_and_validates(admin, bare):
    t = mint(admin, "full")
    err, out = call(bare, t, "update_config", patch={"general": {"language": "en"}})
    assert not err and out["version"]
    assert admin.get("/api/v1/admin/config").json()["config"]["general"]["language"] == "en"
    err, text = call(bare, t, "update_config", patch={"general": {"language": "klingon"}})
    assert err and "language" in text


def test_collections_upsert_partial_update_and_delete(admin, bare):
    t = mint(admin, "full")
    err, out = call(bare, t, "upsert_collection_item", collection="people", item={"name": "Lucía", "color": "#ff8800"})
    assert not err and out["created"] and out["item"]["id"] == "lucia"
    err, out = call(bare, t, "upsert_collection_item", collection="people", item={"id": "lucia", "color": "#112233"})
    assert not err and not out["created"] and out["item"]["name"] == "Lucía" and out["item"]["color"] == "#112233"
    err, out = call(bare, t, "upsert_collection_item", collection="people", item={"name": "Lucía"})
    assert out["item"]["id"] == "lucia-2"
    err, out = call(bare, t, "delete_collection_item", collection="people", id="lucia-2")
    assert not err
    err, text = call(bare, t, "delete_collection_item", collection="people", id="ghost")
    assert err and "ghost" in text


def test_menu_tools_build_a_week_and_rotate(admin, bare):
    t = mint(admin, "full")
    err, out = call(bare, t, "set_menu_day", week=1, day="lunes", meals={"lunch": "Lentejas"})
    assert not err and out["data"]["days"][0]["lunch"] == "Lentejas"
    err, out = call(bare, t, "set_menu_day", week=2, day=6, meals={"dinner": "Pizza"})
    assert not err and out["week"] == 2
    err, text = call(bare, t, "set_menu_day", week=9, day=0, meals={"lunch": "x"})
    assert err and "week debe" in text
    err, out = call(bare, t, "set_current_menu_week", week=2)
    assert not err and out["current"]["number"] == 2 and out["next"]["number"] == 1
    err, out = call(bare, t, "set_menu_week", week=1, name="Verano", shared={"midmorning": "Fruta"})
    assert out["data"]["name"] == "Verano" and out["data"]["days"][0]["lunch"] == "Lentejas"
    err, out = call(bare, t, "delete_menu_week", week=2)
    assert out["weeks_left"] == 1


def test_device_tools(paired, bare):
    admin, dev, _ = paired
    t = mint(admin, "full")
    err, devices = call(bare, t, "list_devices")
    assert not err and devices[0]["id"] == dev
    err, out = call(bare, t, "update_device", device_id=dev, config_patch={"photos": {"interval_s": 33}})
    assert not err and out["config"]["photos"]["interval_s"] == 33
    err, out = call(bare, t, "send_device_command", device_id=dev, type="reload")
    assert not err


def test_argument_checking_and_path_safety(admin, bare):
    t = mint(admin, "full")
    err, text = call(bare, t, "get_device")
    assert err and "faltan" in text
    err, text = call(bare, t, "get_status", extra=1)
    assert err and "desconocidos" in text
    for bad in ("..", "../config", "a/b", "x" * 80):
        err, text = call(bare, t, "get_device", device_id=bad)
        assert err and "no válido" in text
    err, text = call(bare, t, "get_device", device_id="does-not-exist")
    assert err and "404" in text


def test_foreign_origin_is_refused(admin, bare):
    t = mint(admin, "read")
    r = rpc(bare, t, "ping", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    assert rpc(bare, t, "ping", headers={"Origin": "http://testserver"}).status_code == 200


def test_config_schema_tool(admin, bare):
    err, out = call(bare, mint(admin, "read"), "get_config_schema")
    assert not err and "menu" in out["global"]["properties"] and "photos" in out["device"]["properties"]
