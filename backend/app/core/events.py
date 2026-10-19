"""In-process pub/sub used for Server-Sent Events. Safe to publish from worker threads."""
import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass(eq=False)
class Subscriber:
    device_id: str
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=200))


class EventBus:
    def __init__(self) -> None:
        self._subs: set[Subscriber] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self.recent: deque = deque(maxlen=200)

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self, device_id: str) -> Subscriber:
        sub = Subscriber(device_id)
        self._subs.add(sub)
        return sub

    def unsubscribe(self, sub: Subscriber) -> None:
        self._subs.discard(sub)

    def connected_devices(self) -> set[str]:
        return {s.device_id for s in self._subs}

    def publish(self, topic: str, data: dict | None = None, device_id: str | None = None) -> None:
        msg = {"topic": topic, "data": data or {}, "ts": time.time()}
        self.recent.append({**msg, "device_id": device_id})
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self._deliver, msg, device_id)

    def _deliver(self, msg: dict, device_id: str | None) -> None:
        for sub in list(self._subs):
            if device_id and sub.device_id != device_id:
                continue
            try:
                sub.queue.put_nowait(msg)
            except asyncio.QueueFull:
                # A stuck consumer just misses events; it resyncs on reconnect.
                pass


def sse_format(msg: dict) -> str:
    return f"event: {msg['topic']}\ndata: {json.dumps(msg['data'], separators=(',', ':'))}\n\n"


bus = EventBus()
