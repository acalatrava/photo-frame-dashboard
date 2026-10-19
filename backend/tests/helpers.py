import time


def wait_for(fn, timeout=8.0, step=0.1):
    end = time.time() + timeout
    while time.time() < end:
        val = fn()
        if val:
            return val
        time.sleep(step)
    raise AssertionError("condition not reached in time")


def set_config(admin, **sections):
    cfg = admin.get("/api/v1/admin/config").json()["config"]
    for k, v in sections.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    r = admin.put("/api/v1/admin/config", json=cfg)
    assert r.status_code == 200, r.text
    return cfg


def connect_ha(admin, mock, authorized=("light.salon", "light.cocina", "switch.enchufe", "climate.salon",
                                        "sensor.temp_salon", "scene.cine", "script.buenas_noches", "lock.puerta")):
    from tests.mock_ha import TOKEN
    set_config(admin, homeassistant={"enabled": True, "url": mock.url, "authorized_entities": list(authorized)})
    assert admin.put("/api/v1/admin/homeassistant/token", json={"token": TOKEN}).status_code == 200
    wait_for(lambda: admin.get("/health").json()["homeassistant"])
