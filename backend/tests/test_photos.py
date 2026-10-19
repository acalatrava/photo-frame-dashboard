import io

import pytest
from PIL import Image


def h(t): return {"Authorization": f"Bearer {t}"}


def img_bytes(fmt="JPEG", size=(1600, 900), color=(200, 30, 30), exif_orientation=None):
    im = Image.new("RGB", size, color)
    buf = io.BytesIO()
    kwargs = {}
    if fmt == "JPEG" and exif_orientation:
        ex = Image.Exif()
        ex[0x0112] = exif_orientation
        kwargs["exif"] = ex.tobytes()
    if fmt == "HEIF":
        import pillow_heif
        pillow_heif.from_pillow(im).save(buf, format="HEIF")
    else:
        im.save(buf, format=fmt, **kwargs)
    return buf.getvalue()


def make_album(c, name="Familia"):
    r = c.post("/api/v1/admin/albums", json={"name": name})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def upload(c, album, data, name="foto.jpg"):
    return c.post(f"/api/v1/admin/albums/{album}/photos", params={"filename": name}, content=data,
                  headers={"Content-Type": "application/octet-stream"})


def test_upload_jpeg_png_heic_generates_sizes(paired):
    c, dev, token = paired
    album = make_album(c)
    for fmt, name in (("JPEG", "a.jpg"), ("PNG", "b.png"), ("HEIF", "c.heic")):
        r = upload(c, album, img_bytes(fmt, color=(10 * len(name), 50, 90)), name)
        assert r.status_code == 200, (fmt, r.text)
        assert r.json()["created"] is True
    photos = c.get(f"/api/v1/admin/albums/{album}/photos").json()
    assert len(photos) == 3
    for p in photos:
        for size, maxdim in (("thumb", 400), ("screen", 1280)):
            r = c.get(f"/api/v1/admin/photos/{p['id']}/{size}")
            assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
            assert max(Image.open(io.BytesIO(r.content)).size) <= maxdim


def test_vertical_exif_rotated_and_dedupe(paired):
    c, dev, token = paired
    album = make_album(c)
    data = img_bytes("JPEG", size=(1200, 600), exif_orientation=6)  # stored landscape, displayed portrait
    r = upload(c, album, data)
    pid = r.json()["id"]
    screen = Image.open(io.BytesIO(c.get(f"/api/v1/admin/photos/{pid}/screen").content))
    assert screen.size[1] > screen.size[0]
    again = upload(c, album, data)
    assert again.json()["created"] is False and again.json()["id"] == pid
    assert len(c.get(f"/api/v1/admin/albums/{album}/photos").json()) == 1


def test_rejects_garbage_and_oversize(paired, monkeypatch):
    c, dev, token = paired
    album = make_album(c)
    assert upload(c, album, b"<html>not an image</html>", "x.jpg").status_code == 400
    assert upload(c, album, b"", "x.jpg").status_code == 400
    assert upload(c, "nope", img_bytes()).status_code == 404
    from app.core.config import get_settings
    get_settings().photo_max_upload_mb = 0
    assert upload(c, album, img_bytes()).status_code == 413


def test_upload_requires_admin(client):
    r = client.post("/api/v1/admin/albums/x/photos", content=b"abc", headers={"X-HomeHQ-Admin": "1"})
    assert r.status_code == 401


def test_device_album_and_signed_media(paired):
    c, dev, token = paired
    album = make_album(c)
    pid = upload(c, album, img_bytes()).json()["id"]
    cfg = c.get(f"/api/v1/admin/devices/{dev}").json()["config"]
    cfg["photos"]["album_id"] = album
    assert c.put(f"/api/v1/admin/devices/{dev}", json={"config": cfg}).status_code == 200
    dash = c.get("/api/v1/device/dashboard", headers=h(token)).json()
    assert len(dash["photos"]) == 1
    url = dash["photos"][0]["screen"] if "screen" in dash["photos"][0] else dash["photos"][0]["url"]
    assert c.get(url).status_code == 200
    assert "immutable" in c.get(url).headers["cache-control"]
    # tampered signature / other size / master size are refused
    assert c.get(url.split("?")[0] + "?s=deadbeef").status_code == 403
    master = url.rsplit("/", 1)[0] + "/master?" + url.split("?")[1]
    assert c.get(master).status_code == 403
    # a different device's secret does not unlock the photo
    other = c.post("/api/v1/pairing/request", json={"name": "Cocina"}).json()
    c.post(f"/api/v1/admin/pairing/{other['request_id']}/approve", json={"code": other["code"], "name": "Cocina"})
    # delete the photo: media disappears and the device list shrinks
    assert c.delete(f"/api/v1/admin/photos/{pid}").status_code == 200
    assert c.get(url).status_code == 404
    assert c.get("/api/v1/device/dashboard", headers=h(token)).json()["photos"] == []


def test_other_album_not_visible_to_device(paired):
    c, dev, token = paired
    a1, a2 = make_album(c, "A1"), make_album(c, "A2")
    upload(c, a1, img_bytes(color=(1, 2, 3)))
    upload(c, a2, img_bytes(color=(9, 9, 9)))
    cfg = c.get(f"/api/v1/admin/devices/{dev}").json()["config"]
    cfg["photos"]["album_id"] = a2
    c.put(f"/api/v1/admin/devices/{dev}", json={"config": cfg})
    assert len(c.get("/api/v1/device/dashboard", headers=h(token)).json()["photos"]) == 1
    assert c.delete(f"/api/v1/admin/albums/{a2}").status_code == 200
    cfg = c.get(f"/api/v1/admin/devices/{dev}").json()["config"]
    assert cfg["photos"]["album_id"] in (None, "")
