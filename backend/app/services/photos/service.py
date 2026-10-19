"""Photo albums managed from the admin panel (upload based).

Every upload is validated, orientation-corrected, de-duplicated by content hash and stored as a
bounded-size master JPEG plus two derived sizes tuned for a 1280x800 WebView 106 screen.
HEIC/HEIF is converted here, so the frame only ever receives plain JPEG.
"""
import hashlib
import io
import secrets as pysecrets
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from ...core import security
from ...core.config import get_settings
from ...models import Album, Device, Photo

try:  # HEIC support is optional at import time so the service still starts without the wheel.
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF = True
except Exception:  # noqa: BLE001
    HEIF = False

Image.MAX_IMAGE_PIXELS = 120_000_000
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "MPO", "HEIF", "HEIC"}
SIZES = {"master": (2560, 2560, 90), "screen": (1280, 800, 82), "thumb": (400, 400, 75)}


class PhotoError(Exception):
    pass


def album_dir(album_id: str) -> Path:
    return get_settings().photos_dir / album_id


def file_path(album_id: str, photo_id: str, size: str) -> Path:
    if size not in SIZES:
        raise PhotoError("tamaño desconocido")
    return album_dir(album_id) / f"{photo_id}.{size}.jpg"


def create_album(db: Session, name: str) -> Album:
    name = name.strip()
    if not name:
        raise PhotoError("El nombre no puede estar vacío")
    if db.query(Album).filter(Album.name == name).first():
        raise PhotoError("Ya existe un álbum con ese nombre")
    album = Album(id=pysecrets.token_hex(6), name=name)
    db.add(album)
    db.flush()
    album_dir(album.id).mkdir(parents=True, exist_ok=True)
    return album


def delete_album(db: Session, album: Album) -> None:
    shutil.rmtree(album_dir(album.id), ignore_errors=True)
    db.query(Photo).filter(Photo.album_id == album.id).delete()
    db.delete(album)
    # Devices pointing at the removed album simply fall back to "no album".
    for d in db.query(Device).all():
        cfg = dict(d.config or {})
        if cfg.get("photos", {}).get("album_id") == album.id:
            cfg["photos"] = {**cfg["photos"], "album_id": None}
            d.config = cfg
            d.config_version += 1
    db.flush()


def _exif_date(img: Image.Image) -> datetime | None:
    try:
        exif = img.getexif()
        raw = exif.get_ifd(0x8769).get(0x9003) or exif.get(0x0132)
        if raw:
            return datetime.strptime(str(raw), "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:  # noqa: BLE001 - metadata is best effort
        return None
    return None


def _save_jpeg(img: Image.Image, path: Path, box: tuple[int, int], quality: int) -> None:
    out = img.copy()
    out.thumbnail(box, Image.LANCZOS)
    if out.mode != "RGB":
        out = out.convert("RGB")
    out.save(path, "JPEG", quality=quality, optimize=True, progressive=False)


def add_photo(db: Session, album: Album, data: bytes, filename: str) -> tuple[Photo, bool]:
    """Returns (photo, created). A byte-identical upload returns the existing photo."""
    s = get_settings()
    if len(data) > s.photo_max_upload_mb * 1024 * 1024:
        raise PhotoError(f"La foto supera {s.photo_max_upload_mb} MB")
    digest = hashlib.sha256(data).hexdigest()
    dup = db.query(Photo).filter(Photo.album_id == album.id, Photo.sha256 == digest).first()
    if dup:
        return dup, False
    try:
        img = Image.open(io.BytesIO(data))
        fmt = (img.format or "").upper()
        if fmt not in ALLOWED_FORMATS:
            raise PhotoError("Formato no admitido (usa JPEG, PNG, WEBP o HEIC)")
        taken = _exif_date(img)
        img = ImageOps.exif_transpose(img)
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, SyntaxError) as exc:
        raise PhotoError("No se pudo leer la imagen") from exc
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (0, 0, 0))
        rgba = img.convert("RGBA")
        bg.paste(rgba, mask=rgba.split()[3])
        img = bg
    photo_id = pysecrets.token_hex(8)
    album_dir(album.id).mkdir(parents=True, exist_ok=True)
    for size, (w, h, q) in SIZES.items():
        _save_jpeg(img, file_path(album.id, photo_id, size), (w, h), q)
    position = db.query(Photo).filter(Photo.album_id == album.id).count() + 1
    photo = Photo(
        id=photo_id, album_id=album.id, filename=Path(filename).name[:255] or "foto.jpg", sha256=digest,
        width=img.width, height=img.height, taken_at=taken, position=position, size_bytes=len(data),
    )
    db.add(photo)
    db.flush()
    return photo, True


def delete_photo(db: Session, photo: Photo) -> None:
    for size in SIZES:
        file_path(photo.album_id, photo.id, size).unlink(missing_ok=True)
    db.delete(photo)
    db.flush()


def photo_dict(p: Photo) -> dict:
    when = p.taken_at or p.created_at
    return {
        "id": p.id, "album_id": p.album_id, "filename": p.filename, "width": p.width, "height": p.height,
        "o": "p" if p.height > p.width else "l", "date": when.strftime("%Y-%m-%d"), "caption": p.caption,
        "taken_at": p.taken_at.isoformat() if p.taken_at else None,
    }


def signed_url(device: Device, photo: Photo, size: str) -> str:
    path = f"/media/p/{device.id}/{photo.id}/{size}"
    return f"{path}?s={security.media_signature(device.media_secret, path)}"


def device_photos(db: Session, device: Device, album_id: str | None, limit: int = 600) -> list[dict]:
    if not album_id:
        return []
    rows = db.query(Photo).filter(Photo.album_id == album_id).order_by(Photo.position).limit(limit).all()
    out = []
    for p in rows:
        d = photo_dict(p)
        d["thumb"] = signed_url(device, p, "thumb")
        d["screen"] = signed_url(device, p, "screen")
        out.append(d)
    return out
