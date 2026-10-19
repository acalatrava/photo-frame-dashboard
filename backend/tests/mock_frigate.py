"""A tiny fake Frigate: /api/config and /api/<camera>/latest.jpg. NOT a real Frigate."""
import threading
import time

import uvicorn
from fastapi import FastAPI, HTTPException, Response

from tests.mock_ha import jpeg_bytes


class MockFrigate:
    def __init__(self, cameras=("patio", "entrada")):
        self.cameras = list(cameras)
        self.frames = 0
        self.app = FastAPI()
        app = self.app

        @app.get("/api/config")
        def config():
            return {"cameras": {c: {} for c in self.cameras}}

        @app.get("/api/{camera}/latest.jpg")
        def latest(camera: str, h: int = 0):
            if camera not in self.cameras:
                raise HTTPException(404)
            self.frames += 1
            return Response(jpeg_bytes(self.frames), media_type="image/jpeg")

        self.server = None
        self.thread = None
        self.port = 0

    def start(self):
        self.server = uvicorn.Server(uvicorn.Config(self.app, host="127.0.0.1", port=0, log_level="warning"))
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        while not self.server.started:
            time.sleep(0.05)
        self.port = self.server.servers[0].sockets[0].getsockname()[1]
        return self

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def stop(self):
        self.server.should_exit = True
        self.thread.join(timeout=5)
