def h(t): return {"Authorization": f"Bearer {t}"}


def ops(c, token, lst):
    r = c.post("/api/v1/device/shopping/ops", headers=h(token), json={"ops": lst})
    assert r.status_code == 200, r.text
    return r.json()


def test_local_provider_flow_and_dedupe(paired):
    c, dev, token = paired
    res = ops(c, token, [
        {"op_id": "o-000001", "type": "add", "name": "Leche"},
        {"op_id": "o-000002", "type": "add", "name": "Huevos", "client_id": "tmp-a"},
        {"op_id": "o-000003", "type": "add", "name": "LECHE"},
        {"op_id": "o-000004", "type": "add", "name": "Café"},
        {"op_id": "o-000005", "type": "add", "name": "cafe"},
        {"op_id": "o-000006", "type": "set_done", "id": "tmp-a", "done": True},
    ])
    items = res["shopping"]["items"]
    assert sorted(i["name"] for i in items) == ["Café", "Huevos", "Leche"]
    assert [i["name"] for i in items if i["done"]] == ["Huevos"]
    assert items[-1]["done"] is True  # pending first, completed last
    # re-adding a completed item re-opens it instead of duplicating
    res = ops(c, token, [{"op_id": "o-000007", "type": "add", "name": "huevos"}])
    assert all(not i["done"] for i in res["shopping"]["items"]) and len(res["shopping"]["items"]) == 3
    # idempotent replay and ops on removed items are harmless
    eid = next(i["id"] for i in res["shopping"]["items"] if i["name"] == "Leche")
    ops(c, token, [{"op_id": "o-000008", "type": "remove", "id": eid}])
    res = ops(c, token, [{"op_id": "o-000009", "type": "set_done", "id": eid, "done": True},
                         {"op_id": "o-000008", "type": "remove", "id": eid}])
    assert res["results"][0]["noop"] is True and res["results"][1]["replayed"] is True
    assert sorted(i["name"] for i in res["shopping"]["items"]) == ["Café", "Huevos"]


def test_rename_and_validation(paired):
    c, dev, token = paired
    res = ops(c, token, [{"op_id": "o-100001", "type": "add", "name": "Pan"}])
    pid = res["shopping"]["items"][0]["id"]
    res = ops(c, token, [{"op_id": "o-100002", "type": "rename", "id": pid, "name": "Pan integral"}])
    assert res["shopping"]["items"][0]["name"] == "Pan integral"
    bad = c.post("/api/v1/device/shopping/ops", headers=h(token), json={"ops": [{"op_id": "o-100003", "type": "add"}]})
    assert bad.status_code in (400, 422)
    bad = c.post("/api/v1/device/shopping/ops", headers=h(token),
                 json={"ops": [{"op_id": "o-100004", "type": "explode", "name": "x"}]})
    assert bad.status_code == 422
