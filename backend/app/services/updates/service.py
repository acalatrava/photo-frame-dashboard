"""App releases the frames can install over the network.

Each uploaded APK lives in `<data>/updates/<versionCode>/` with its metadata; `published.json` says which one
frames are offered. Nothing here touches the database, so the folder can be copied or inspected by hand.
"""
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

from ...core.config import get_settings
from . import apk

APK_PACKAGE = "com.wesbos.homehq"
_MAX_NOTES = 500


class UpdateError(Exception):
    def __init__(self, msg: str, status: int = 400):
        super().__init__(msg)
        self.msg, self.status = msg, status


def _root() -> Path:
    root = get_settings().updates_dir
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _meta(version_code: int) -> dict | None:
    try:
        return json.loads((_root() / str(version_code) / "meta.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def list_releases() -> list[dict]:
    out = []
    for d in _root().iterdir():
        if d.is_dir() and d.name.isdigit():
            m = _meta(int(d.name))
            if m:
                out.append(m)
    return sorted(out, key=lambda m: m["version_code"], reverse=True)


def published_code() -> int | None:
    try:
        return int(json.loads((_root() / "published.json").read_text(encoding="utf-8"))["version_code"])
    except (FileNotFoundError, ValueError, KeyError):
        return None


def published() -> dict | None:
    code = published_code()
    return _meta(code) if code is not None else None


def apk_path(version_code: int) -> Path:
    return _root() / str(version_code) / "homehq.apk"


def add_release(data: bytes, filename: str, notes: str = "") -> tuple[dict, bool]:
    """Validates and stores an APK. Returns (release, created); re-uploading the same file is a no-op."""
    try:
        info = apk.inspect(data)
    except apk.ApkError as exc:
        raise UpdateError(str(exc)) from exc
    if info.package != APK_PACKAGE:
        raise UpdateError(f"El APK es de «{info.package}», no de {APK_PACKAGE}")
    if info.version_code < 1:
        raise UpdateError("El APK no tiene un versionCode válido")
    sha = hashlib.sha256(data).hexdigest()
    current = _meta(info.version_code)
    if current:
        if current["sha256"] == sha:
            return current, False
        raise UpdateError(f"Ya existe la versión {info.version_code} con otro contenido: sube el APK con un versionCode mayor", 409)
    # Android refuses to update an app with a different signing certificate, so reject it here rather than
    # letting every frame download something it can never install.
    known = {m["cert_sha256"] for m in list_releases() if m["cert_sha256"]}
    if known and info.cert_sha256 not in known:
        raise UpdateError("El APK está firmado con otra clave que las versiones anteriores: los marcos no podrían instalarlo")
    folder = _root() / str(info.version_code)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "homehq.apk").write_bytes(data)
    meta = {
        "version_code": info.version_code, "version_name": info.version_name, "package": info.package,
        "size": len(data), "sha256": sha, "cert_sha256": info.cert_sha256,
        "notes": notes.strip()[:_MAX_NOTES], "filename": os.path.basename(filename)[:120],
        "uploaded_at": time.time(),
    }
    _write_json(folder / "meta.json", meta)
    return meta, True


def publish(version_code: int) -> dict:
    m = _meta(version_code)
    if not m:
        raise UpdateError("Versión no encontrada", 404)
    _write_json(_root() / "published.json", {"version_code": version_code, "at": time.time()})
    return m


def unpublish() -> None:
    try:
        (_root() / "published.json").unlink()
    except FileNotFoundError:
        pass


def delete(version_code: int) -> None:
    if not _meta(version_code):
        raise UpdateError("Versión no encontrada", 404)
    if published_code() == version_code:
        raise UpdateError("Retira la publicación antes de borrar esta versión", 409)
    shutil.rmtree(_root() / str(version_code), ignore_errors=True)


def public_view(m: dict | None) -> dict | None:
    """What frames and the admin panel see of a release."""
    if not m:
        return None
    return {k: m[k] for k in ("version_code", "version_name", "size", "sha256", "cert_sha256", "notes", "uploaded_at")}
