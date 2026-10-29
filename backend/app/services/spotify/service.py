"""Spotify through its Web API (Authorization Code with PKCE, so no client secret is stored).

The frame does not play audio itself: it controls Spotify Connect speakers (Echo, Sonos, Chromecast, a phone...) and
shows what is playing. The refresh token lives encrypted in the secrets table; access tokens only in memory.
"""
import base64
import hashlib
import logging
import re
import secrets
import threading
import time
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from ...core import secrets_store
from ...core.db import session_scope

log = logging.getLogger("homehq.spotify")

ACCOUNTS = "https://accounts.spotify.com"
API = "https://api.spotify.com/v1"
SECRET = "spotify.refresh_token"
SCOPES = ("user-read-playback-state user-modify-playback-state user-read-currently-playing "
          "playlist-read-private playlist-read-collaborative")

URI = re.compile(r"^spotify:(track|album|playlist|artist|episode|show):[A-Za-z0-9]{10,40}$")
DEVICE = re.compile(r"^[A-Za-z0-9_\-]{10,80}$")

_lock = threading.Lock()
_pending: dict[str, tuple[str, float]] = {}
_access = {"token": "", "exp": 0.0}


class SpotifyError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _client() -> httpx.Client:
    return httpx.Client(timeout=10, follow_redirects=False)


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


# ------------------------------------------------------------------ connecting the account
def authorize_url(client_id: str, redirect_uri: str) -> str:
    if not client_id:
        raise SpotifyError(400, "Falta el Client ID de la aplicación de Spotify")
    verifier = _b64(secrets.token_bytes(48))
    state = secrets.token_urlsafe(16)
    now = time.time()
    with _lock:
        for k in [k for k, (_, exp) in _pending.items() if exp < now]:
            del _pending[k]
        _pending[state] = (verifier, now + 900)
    return f"{ACCOUNTS}/authorize?" + urlencode({
        "client_id": client_id, "response_type": "code", "redirect_uri": redirect_uri, "scope": SCOPES,
        "state": state, "code_challenge_method": "S256",
        "code_challenge": _b64(hashlib.sha256(verifier.encode()).digest())})


def _parse_code(pasted: str) -> tuple[str, str | None]:
    """Accepts the whole address Spotify redirected to, or just the code in it."""
    pasted = pasted.strip()
    if "code=" in pasted:
        query = parse_qs(urlparse(pasted).query or pasted.split("?", 1)[-1])
        if query.get("error"):
            raise SpotifyError(400, "Spotify rechazó el permiso: " + query["error"][0])
        return (query.get("code") or [""])[0], (query.get("state") or [None])[0]
    return pasted, None


def connect(client_id: str, redirect_uri: str, pasted: str) -> None:
    code, state = _parse_code(pasted)
    if not code:
        raise SpotifyError(400, "No se encontró el código en lo que has pegado")
    with _lock:
        if state is not None:
            entry = _pending.pop(state, None)
        else:
            entry = _pending.pop(max(_pending, key=lambda k: _pending[k][1]), None) if _pending else None
    if not entry or entry[1] < time.time():
        raise SpotifyError(400, "La autorización ha caducado o no se inició desde aquí. Vuelve a pulsar «Conectar».")
    with _client() as c:
        r = c.post(f"{ACCOUNTS}/api/token", data={
            "grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri,
            "client_id": client_id, "code_verifier": entry[0]})
    body = _json(r)
    if r.status_code != 200 or not body.get("refresh_token"):
        raise SpotifyError(400, "Spotify no aceptó el código: " + str(body.get("error_description") or body.get("error") or r.status_code))
    with session_scope() as db:
        secrets_store.set_secret(db, SECRET, body["refresh_token"])
    _access.update(token=body["access_token"], exp=time.time() + int(body.get("expires_in", 3600)) - 60)


def disconnect() -> None:
    with session_scope() as db:
        secrets_store.delete_secret(db, SECRET)
    _access.update(token="", exp=0.0)


def connected() -> bool:
    with session_scope() as db:
        return secrets_store.has_secret(db, SECRET)


def _json(r: httpx.Response) -> dict:
    try:
        v = r.json()
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


# ------------------------------------------------------------------ calling the API
def access_token(client_id: str) -> str:
    if _access["token"] and _access["exp"] > time.time():
        return _access["token"]
    with session_scope() as db:
        refresh = secrets_store.get_secret(db, SECRET)
    if not refresh:
        raise SpotifyError(409, "Spotify no está conectado")
    with _client() as c:
        r = c.post(f"{ACCOUNTS}/api/token", data={"grant_type": "refresh_token", "refresh_token": refresh, "client_id": client_id})
    body = _json(r)
    if r.status_code == 400 and body.get("error") == "invalid_grant":
        disconnect()
        raise SpotifyError(409, "La conexión con Spotify ha caducado: vuelve a conectarla desde el panel")
    if r.status_code != 200 or not body.get("access_token"):
        raise SpotifyError(502, "No se pudo renovar el acceso a Spotify")
    if body.get("refresh_token") and body["refresh_token"] != refresh:
        with session_scope() as db:
            secrets_store.set_secret(db, SECRET, body["refresh_token"])
    _access.update(token=body["access_token"], exp=time.time() + int(body.get("expires_in", 3600)) - 60)
    return _access["token"]


def call(client_id: str, method: str, path: str, params: dict | None = None, body: dict | None = None,
         _retry: bool = True) -> dict | None:
    token = access_token(client_id)
    with _client() as c:
        r = c.request(method, API + path, params=params, json=body, headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 401 and _retry:
        _access.update(token="", exp=0.0)
        return call(client_id, method, path, params, body, _retry=False)
    if r.status_code == 429:
        raise SpotifyError(429, "Spotify pide esperar unos segundos")
    if r.status_code in (200, 201) and r.content:
        return _json(r)
    if r.status_code < 300:
        return None
    msg = (_json(r).get("error") or {})
    msg = msg.get("message") if isinstance(msg, dict) else str(msg)
    if r.status_code == 404 and "device" in (msg or "").lower():
        msg = "No hay ningún altavoz de Spotify activo. Abre Spotify en uno o elígelo en la lista."
    if r.status_code == 403:
        msg = msg or "Spotify exige una cuenta Premium para controlar la reproducción"
    raise SpotifyError(r.status_code if r.status_code in (403, 404) else 502, msg or f"Spotify respondió {r.status_code}")


# ------------------------------------------------------------------ what the frame needs
def _art(images: list | None, want: int = 300) -> str:
    imgs = [i for i in (images or []) if isinstance(i, dict) and i.get("url")]
    if not imgs:
        return ""
    best = min(imgs, key=lambda i: abs((i.get("width") or want) - want))
    return best["url"]


def playback(client_id: str) -> dict:
    p = call(client_id, "GET", "/me/player", params={"additional_types": "episode"})
    if not p or not p.get("device"):
        return {"active": False}
    item = p.get("item") or {}
    album = item.get("album") or item.get("show") or {}
    artists = ", ".join(a.get("name", "") for a in item.get("artists", []) if isinstance(a, dict)) or album.get("publisher", "")
    dev = p["device"]
    return {
        "active": True, "playing": bool(p.get("is_playing")), "progress_ms": p.get("progress_ms") or 0,
        "device": {"id": dev.get("id"), "name": dev.get("name"), "type": dev.get("type"), "volume": dev.get("volume_percent")},
        "track": {"name": item.get("name", ""), "artists": artists, "album": album.get("name", ""), "uri": item.get("uri", ""),
                  "duration_ms": item.get("duration_ms") or 0, "art": _art(album.get("images"))} if item else None,
    }


def devices(client_id: str) -> list[dict]:
    d = call(client_id, "GET", "/me/player/devices") or {}
    return [{"id": x.get("id"), "name": x.get("name"), "type": x.get("type"), "active": bool(x.get("is_active")),
             "volume": x.get("volume_percent"), "restricted": bool(x.get("is_restricted"))}
            for x in d.get("devices", []) if x.get("id")]


def playlists(client_id: str) -> list[dict]:
    d = call(client_id, "GET", "/me/playlists", params={"limit": 40}) or {}
    return [{"kind": "playlist", "name": p.get("name", ""), "sub": (p.get("owner") or {}).get("display_name", ""),
             "uri": p.get("uri", ""), "art": _art(p.get("images"), 200)}
            for p in d.get("items", []) if isinstance(p, dict) and p.get("uri")]


def search(client_id: str, q: str) -> list[dict]:
    d = call(client_id, "GET", "/search", params={"q": q, "type": "track,album,playlist", "limit": 8}) or {}
    out = []
    for t in (d.get("tracks") or {}).get("items", []):
        if t:
            out.append({"kind": "track", "name": t.get("name", ""), "uri": t.get("uri", ""),
                        "sub": ", ".join(a.get("name", "") for a in t.get("artists", [])), "art": _art((t.get("album") or {}).get("images"), 200)})
    for a in (d.get("albums") or {}).get("items", []):
        if a:
            out.append({"kind": "album", "name": a.get("name", ""), "uri": a.get("uri", ""),
                        "sub": ", ".join(x.get("name", "") for x in a.get("artists", [])), "art": _art(a.get("images"), 200)})
    for p in (d.get("playlists") or {}).get("items", []):
        if p:
            out.append({"kind": "playlist", "name": p.get("name", ""), "uri": p.get("uri", ""),
                        "sub": (p.get("owner") or {}).get("display_name", ""), "art": _art(p.get("images"), 200)})
    return [o for o in out if URI.match(o["uri"])]


def control(client_id: str, action: str, device_id: str | None = None, uri: str | None = None,
            volume: int | None = None) -> None:
    if device_id and not DEVICE.match(device_id):
        raise SpotifyError(422, "Altavoz no válido")
    if uri and not URI.match(uri):
        raise SpotifyError(422, "Elemento de Spotify no válido")
    dev = {"device_id": device_id} if device_id else None
    if action == "pause":
        call(client_id, "PUT", "/me/player/pause", params=dev)
    elif action == "next":
        call(client_id, "POST", "/me/player/next", params=dev)
    elif action == "previous":
        call(client_id, "POST", "/me/player/previous", params=dev)
    elif action == "volume":
        if volume is None or not 0 <= volume <= 100:
            raise SpotifyError(422, "Volumen entre 0 y 100")
        call(client_id, "PUT", "/me/player/volume", params={**(dev or {}), "volume_percent": volume})
    elif action == "transfer":
        if not device_id:
            raise SpotifyError(422, "Falta el altavoz")
        call(client_id, "PUT", "/me/player", body={"device_ids": [device_id], "play": True})
    elif action == "play":
        body = None
        if uri:
            body = {"uris": [uri]} if uri.startswith(("spotify:track:", "spotify:episode:")) else {"context_uri": uri}
        call(client_id, "PUT", "/me/player/play", params=dev, body=body)
    else:
        raise SpotifyError(422, "Acción no válida")
