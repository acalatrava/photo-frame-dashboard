import hashlib
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization

from app.services.updates import apk
from tests.apkbuild import build_apk, new_identity


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def fingerprint(cert):
    return hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).hexdigest()


@pytest.fixture(scope="module")
def identity():
    return new_identity()


def upload(admin, data, notes=""):
    return admin.post("/api/v1/admin/updates", params={"filename": "homehq.apk", "notes": notes}, content=data,
                      headers={"Content-Type": "application/octet-stream"})


@pytest.mark.parametrize("utf8", [False, True])
def test_apk_inspection_reads_package_version_and_certificate(identity, utf8):
    data, cert = build_apk(version_code=42, version_name="3.1-beta", identity=identity, utf8=utf8)
    info = apk.inspect(data)
    assert (info.package, info.version_code, info.version_name) == ("com.wesbos.homehq", 42, "3.1-beta")
    assert info.cert_sha256 == fingerprint(cert)


def test_apk_inspection_rejects_garbage():
    for bad in (b"", b"not a zip", b"PK\x05\x06" + b"\0" * 18):
        with pytest.raises(apk.ApkError):
            apk.inspect(bad)


@pytest.mark.skipif(not Path(__file__).parents[2].joinpath("dashboard/kiosk/build/homehq.apk").exists(),
                    reason="the kiosk APK has not been built")
def test_real_kiosk_apk_is_understood():
    info = apk.inspect(Path(__file__).parents[2].joinpath("dashboard/kiosk/build/homehq.apk").read_bytes())
    assert info.package == "com.wesbos.homehq" and info.version_code >= 1 and len(info.cert_sha256) == 64


def test_upload_publish_and_download(paired, identity):
    admin, _, token = paired
    data, cert = build_apk(version_code=7, version_name="2.4", identity=identity)
    r = upload(admin, data, "Cambios de prueba")
    assert r.status_code == 200 and r.json()["created"] is True
    assert r.json()["release"]["cert_sha256"] == fingerprint(cert)

    # Uploaded but not published: frames are told there is nothing.
    info = admin.get("/api/v1/device/update", headers=auth(token)).json()
    assert info["release"] is None and info["mode"] == "notify" and info["package"] == "com.wesbos.homehq"
    assert admin.get("/api/v1/device/update/apk", headers=auth(token)).status_code == 404

    overview = admin.post("/api/v1/admin/updates/7/publish").json()
    assert overview["published"] == 7 and overview["releases"][0]["version_name"] == "2.4"

    info = admin.get("/api/v1/device/update", headers=auth(token)).json()["release"]
    assert info["version_code"] == 7 and info["sha256"] == hashlib.sha256(data).hexdigest()
    assert info["size"] == len(data) and info["notes"] == "Cambios de prueba"

    got = admin.get("/api/v1/device/update/apk", headers=auth(token))
    assert got.status_code == 200 and got.content == data
    assert got.headers["x-homehq-version-code"] == "7"
    assert got.headers["content-type"] == "application/vnd.android.package-archive"


def test_downloads_need_a_paired_device(paired, identity):
    admin, _, _ = paired
    upload(admin, build_apk(identity=identity)[0])
    admin.post("/api/v1/admin/updates/7/publish")
    from fastapi.testclient import TestClient
    anon = TestClient(admin.app)
    assert anon.get("/api/v1/device/update").status_code == 401
    assert anon.get("/api/v1/device/update/apk").status_code == 401
    assert anon.get("/api/v1/admin/updates").status_code in (401, 403)


def test_upload_validation(admin, identity):
    assert upload(admin, b"hello").status_code == 400
    other, _ = build_apk(package="com.example.other", identity=identity)
    r = upload(admin, other)
    assert r.status_code == 400 and "com.example.other" in r.json()["detail"]

    data, _ = build_apk(version_code=7, identity=identity, payload=b"a")
    assert upload(admin, data).json()["created"] is True
    again = upload(admin, data)
    assert again.status_code == 200 and again.json()["created"] is False
    clash, _ = build_apk(version_code=7, identity=identity, payload=b"b")
    assert upload(admin, clash).status_code == 409

    foreign, _ = build_apk(version_code=8, identity=new_identity("Someone else"))
    r = upload(admin, foreign)
    assert r.status_code == 400 and "firmado con otra clave" in r.json()["detail"]


def test_size_limit(admin, identity, monkeypatch):
    monkeypatch.setenv("HOMEHQ_APK_MAX_UPLOAD_MB", "0")
    from app.core.config import get_settings
    get_settings.cache_clear()
    r = upload(admin, build_apk(identity=identity)[0])
    assert r.status_code == 413
    get_settings.cache_clear()


def test_delete_rules_and_unpublish(admin, identity):
    upload(admin, build_apk(version_code=7, identity=identity)[0])
    upload(admin, build_apk(version_code=8, version_name="2.5", identity=identity)[0])
    admin.post("/api/v1/admin/updates/8/publish")
    assert admin.delete("/api/v1/admin/updates/8").status_code == 409
    assert admin.delete("/api/v1/admin/updates/7").status_code == 200
    assert admin.delete("/api/v1/admin/updates/99").status_code == 404
    assert admin.post("/api/v1/admin/updates/99/publish").status_code == 404
    assert admin.post("/api/v1/admin/updates/unpublish").json()["published"] is None
    assert admin.delete("/api/v1/admin/updates/8").status_code == 200
    assert admin.get("/api/v1/admin/updates").json()["releases"] == []


def test_mode_is_validated_and_reaches_the_frames(paired):
    admin, _, token = paired
    boot = admin.get("/api/v1/device/bootstrap", headers=auth(token)).json()["config"]
    assert boot["updates"] == {"mode": "notify"}
    assert admin.put("/api/v1/admin/updates/settings", json={"mode": "auto"}).json()["mode"] == "auto"
    boot = admin.get("/api/v1/device/bootstrap", headers=auth(token)).json()["config"]
    assert boot["updates"] == {"mode": "auto"}
    assert admin.put("/api/v1/admin/updates/settings", json={"mode": "yolo"}).status_code == 422


def test_update_command_is_accepted(paired):
    admin, device_id, _ = paired
    r = admin.post(f"/api/v1/admin/devices/{device_id}/command", json={"type": "update"})
    assert r.status_code == 200
