"""A tiny stand-in for accounts.spotify.com and api.spotify.com."""
import base64
import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DEVICE = {"id": "a" * 20, "name": "Echo cocina", "type": "Speaker", "is_active": True, "volume_percent": 35}


class MockSpotify:
    def __init__(self):
        self.calls = []
        self.challenge = None
        self.revoked = False
        self.tokens_issued = 0
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, body=None):
                raw = json.dumps(body).encode() if body is not None else b""
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def _body(self):
                n = int(self.headers.get("Content-Length") or 0)
                return self.rfile.read(n).decode() if n else ""

            def do_POST(self):
                if self.path == "/api/token":
                    form = {k: v[0] for k, v in parse_qs(self._body()).items()}
                    outer.calls.append(("TOKEN", form))
                    if form["grant_type"] == "authorization_code":
                        digest = base64.urlsafe_b64encode(hashlib.sha256(form["code_verifier"].encode()).digest()).rstrip(b"=").decode()
                        if form["code"] != "goodcode" or digest != outer.challenge:
                            return self._send(400, {"error": "invalid_grant", "error_description": "bad code"})
                    elif outer.revoked:
                        return self._send(400, {"error": "invalid_grant"})
                    outer.tokens_issued += 1
                    return self._send(200, {"access_token": f"AT{outer.tokens_issued}", "refresh_token": "RT1", "expires_in": 3600})
                self._api("POST")

            def do_GET(self):
                self._api("GET")

            def do_PUT(self):
                self._api("PUT")

            def _api(self, method):
                u = urlparse(self.path)
                body = self._body()
                outer.calls.append((method, u.path, {k: v[0] for k, v in parse_qs(u.query).items()}, body,
                                    self.headers.get("Authorization")))
                if u.path == "/v1/me/player" and method == "GET":
                    return self._send(200, {"is_playing": True, "progress_ms": 1000, "device": DEVICE, "item": {
                        "name": "Canción", "uri": "spotify:track:" + "b" * 22, "duration_ms": 180000,
                        "artists": [{"name": "Ana"}], "album": {"name": "Disco", "images": [{"url": "https://i.scdn.co/image/x", "width": 300}]}}})
                if u.path == "/v1/me/player/devices":
                    return self._send(200, {"devices": [DEVICE]})
                if u.path == "/v1/me/playlists":
                    return self._send(200, {"items": [None, {"name": "Cocina", "uri": "spotify:playlist:" + "c" * 22, "owner": {"display_name": "Yo"}, "images": []}]})
                if u.path == "/v1/search":
                    return self._send(200, {"tracks": {"items": [{"name": "T", "uri": "spotify:track:" + "d" * 22, "artists": [{"name": "A"}], "album": {"images": []}}]},
                                            "albums": {"items": []}, "playlists": {"items": [None]}})
                return self._send(204)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def start(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def stop(self):
        self.httpd.shutdown()
