"""What a tool needs to act: a way to call the admin API as the caller, with the caller's own token.

Tools are thin on purpose. They go through the same HTTP routes as the admin panel, so every validation rule, event
and permission check (including the read-only scope of a token) applies to an agent exactly as it does to a person.
"""
import json
import re
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import FastAPI

MAX_TEXT = 60_000


class ToolError(Exception):
    """A failure the agent should read and can act on (bad input, rejected by validation, not found...)."""


class Ctx:
    def __init__(self, app: FastAPI, authorization: str, scope: str = "read"):
        self.app = app
        self.authorization = authorization
        self.scope = scope

    async def api(self, method: str, path: str, *, params: dict | None = None, body: Any = None) -> Any:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://homehq.internal", timeout=60) as c:
            r = await c.request(method, path, params=params, json=body,
                                headers={"Authorization": self.authorization, "Accept": "application/json"})
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except ValueError:
                detail = r.text
            if isinstance(detail, list):
                detail = "; ".join(f"{'.'.join(str(x) for x in e.get('loc', []))}: {e.get('msg')}" for e in detail)
            raise ToolError(f"{r.status_code}: {detail}")
        if not r.content:
            return {"ok": True}
        try:
            return r.json()
        except ValueError:
            return {"ok": True, "content_type": r.headers.get("content-type", ""), "bytes": len(r.content)}


_SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


def q(value: Any) -> str:
    """A value placed inside a URL path. Dots-only segments are refused so an id can never climb out of its route."""
    text = str(value)
    if not _SAFE_ID.match(text) or set(text) == {"."}:
        raise ToolError(f"Identificador no válido: {text[:40]!r}")
    return quote(text, safe="")


def as_text(data: Any) -> str:
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if len(text) > MAX_TEXT:
        return text[:MAX_TEXT] + f'… [recortado: {len(text)} caracteres en total]'
    return text


def merge_patch(target: Any, patch: Any) -> Any:
    """RFC 7386 JSON Merge Patch: objects merge, `null` removes a key, anything else replaces."""
    if not isinstance(patch, dict):
        return patch
    out = dict(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            out.pop(key, None)
        else:
            out[key] = merge_patch(out.get(key), value)
    return out
