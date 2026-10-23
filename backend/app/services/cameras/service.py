"""Live cameras for the frames: Frigate, Home Assistant camera entities or any snapshot URL.

Frames never talk to the camera system. The backend fetches JPEG snapshots (Frigate `latest.jpg`, Home Assistant's
camera proxy or a plain URL) and republishes them as a multipart MJPEG stream, which a WebView shows in a plain
<img>. That works with every Frigate version, needs no extra ports on the frame and keeps credentials on the server.
"""
import asyncio
import logging
import time
from typing import AsyncIterator

import httpx

from ...core import security
from ...core.http import TooLarge, get_limited
from ...models import Device
from ...schemas.config import CameraSource, GlobalConfig
from ..homeassistant.client import HAClient, HAError

log = logging.getLogger("homehq.cameras")
BOUNDARY = "homehqframe"
MAX_STREAMS = 8
MAX_SNAPSHOT_BYTES = 10 * 1024 * 1024
MAX_STREAM_SECONDS = 15 * 60

_active = 0


class CameraError(Exception):
    pass


def find(g: GlobalConfig, camera_id: str) -> CameraSource | None:
    return next((c for c in g.cameras if c.id == camera_id and c.enabled), None)


def device_list(g: GlobalConfig, device: Device) -> list[dict]:
    out = []
    for c in g.cameras:
        if not c.enabled:
            continue
        base = f"/media/cam/{device.id}/{c.id}"
        sig = lambda kind: f"{base}/{kind}?s={security.media_signature(device.media_secret, f'{base}/{kind}')}"
        out.append({"id": c.id, "name": c.name, "snapshot": sig("snapshot"), "stream": sig("stream")})
    return out


def verify_sig(device: Device, camera_id: str, kind: str, sig: str) -> bool:
    path = f"/media/cam/{device.id}/{camera_id}/{kind}"
    return security.constant_eq(sig, security.media_signature(device.media_secret, path))


async def fetch_snapshot(g: GlobalConfig, cam: CameraSource, ha: HAClient, client: httpx.AsyncClient | None = None
                         ) -> bytes:
    """One JPEG frame from the camera's source."""
    try:
        if cam.source == "ha":
            if not cam.ha_entity or cam.ha_entity not in g.homeassistant.authorized_entities:
                raise CameraError("La cámara de Home Assistant no está autorizada")
            data, _ = await ha.rest_bytes(f"/api/camera_proxy/{cam.ha_entity}", timeout=8)
            return data
        if cam.source == "frigate":
            if not g.frigate.url or not cam.frigate_camera:
                raise CameraError("Frigate no está configurado")
            url = f"{g.frigate.url}/api/{cam.frigate_camera}/latest.jpg?h=720"
            verify = g.frigate.verify_tls
        else:
            if not cam.url:
                raise CameraError("Falta la URL de la imagen")
            url, verify = cam.url, True
        own = client is None
        client = client or httpx.AsyncClient(verify=verify, timeout=8, follow_redirects=True)
        try:
            r = await get_limited(client, url, MAX_SNAPSHOT_BYTES)
        finally:
            if own:
                await client.aclose()
        if r.status_code >= 400:
            raise CameraError(f"La cámara respondió {r.status_code}")
        if not r.headers.get("content-type", "").startswith("image/"):
            raise CameraError("La respuesta no es una imagen")
        return r.content
    except HAError as exc:
        raise CameraError(str(exc)) from exc
    except TooLarge as exc:
        raise CameraError("La imagen de la cámara es demasiado grande") from exc
    except httpx.HTTPError as exc:
        raise CameraError(f"No se pudo conectar con la cámara: {exc.__class__.__name__}") from exc


def _part(frame: bytes) -> bytes:
    return (f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\nContent-Length: {len(frame)}\r\n\r\n").encode() \
        + frame + b"\r\n"


async def mjpeg(g: GlobalConfig, cam: CameraSource, ha: HAClient, is_disconnected, first: bytes | None = None
                ) -> AsyncIterator[bytes]:
    """Multipart MJPEG at the camera's frame rate; ends when the client leaves or after a safety limit."""
    global _active
    if _active >= MAX_STREAMS:
        raise CameraError("Demasiados streams abiertos")
    _active += 1
    period = 1.0 / max(1, cam.fps)
    started = time.monotonic()
    verify = g.frigate.verify_tls if cam.source == "frigate" else True
    client = httpx.AsyncClient(verify=verify, timeout=8, follow_redirects=True) if cam.source != "ha" else None
    failures = 0
    try:
        if first:
            yield _part(first)
        while time.monotonic() - started < MAX_STREAM_SECONDS:
            t0 = time.monotonic()
            if await is_disconnected():
                return
            try:
                frame = await fetch_snapshot(g, cam, ha, client)
                failures = 0
            except CameraError as exc:
                failures += 1
                log.warning("camera %s: %s", cam.id, exc)
                if failures >= 5:
                    return
                await asyncio.sleep(1.0)
                continue
            yield _part(frame)
            await asyncio.sleep(max(0.0, period - (time.monotonic() - t0)))
    finally:
        _active -= 1
        if client:
            await client.aclose()


async def frigate_cameras(g: GlobalConfig) -> list[str]:
    """Camera names configured in Frigate (for the admin panel's picker)."""
    if not g.frigate.url:
        raise CameraError("Indica primero la URL de Frigate")
    try:
        async with httpx.AsyncClient(verify=g.frigate.verify_tls, timeout=8) as c:
            r = await c.get(f"{g.frigate.url}/api/config")
    except httpx.HTTPError as exc:
        raise CameraError(f"No se pudo conectar con Frigate: {exc.__class__.__name__}") from exc
    if r.status_code >= 400:
        raise CameraError(f"Frigate respondió {r.status_code}")
    try:
        return sorted((r.json().get("cameras") or {}).keys())
    except ValueError as exc:
        raise CameraError("Respuesta de Frigate no válida") from exc
