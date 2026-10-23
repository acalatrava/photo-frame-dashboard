"""Model Context Protocol server (Streamable HTTP transport, stateless, JSON responses).

An agent connects to `POST /mcp` with `Authorization: Bearer hqa_...`, the same API token used for the REST admin API.
Nothing here widens access: each tool call is forwarded to the admin API with the caller's own token, so the read-only
scope, validation and events behave exactly as they do for the panel.
"""
import json
import logging
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from ..api.deps import mcp_token_user
from ..core.config import get_settings
from ..core.db import get_db
from .runtime import Ctx, ToolError, as_text
from .tools import TOOLS

log = logging.getLogger("homehq.mcp")
router = APIRouter(tags=["mcp"])

PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"]
MAX_BODY = 1_000_000
INSTRUCTIONS = (
    "Home HQ controla los marcos de fotos de la casa. Empieza con get_status y get_config; lee get_config_schema "
    "antes de escribir. Usa update_config (merge patch) para ajustes, upsert_collection_item para personas, "
    "calendarios, tareas y cámaras, update_device para un marco concreto y set_menu_day / set_menu_week para el menú "
    "semanal. Los secretos son de solo escritura y nunca se devuelven."
)


def _error(rid: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def _origin_ok(request: Request) -> bool:
    """Browsers always send Origin. Scripts and agent clients usually do not, and are let through."""
    origin = request.headers.get("origin")
    if not origin:
        return True
    host = urlparse(origin).netloc
    return host == request.headers.get("host", "") or origin.rstrip("/") in get_settings().cors_list


async def _call(ctx: Ctx, params: dict) -> dict:
    name = params.get("name")
    tool = TOOLS.get(name) if isinstance(name, str) else None
    if not tool:
        raise ValueError(f"Herramienta desconocida: {name!r}")
    args = params.get("arguments") or {}
    if not isinstance(args, dict):
        raise ValueError("arguments debe ser un objeto")
    schema = tool.schema
    unknown = sorted(set(args) - set(schema["properties"]))
    missing = [k for k in schema["required"] if k not in args]
    if unknown or missing:
        text = "; ".join(filter(None, [f"faltan: {', '.join(missing)}" if missing else "",
                                       f"campos desconocidos: {', '.join(unknown)}" if unknown else ""]))
        return {"content": [{"type": "text", "text": text}], "isError": True}
    try:
        data = await tool.handler(ctx, args)
        return {"content": [{"type": "text", "text": as_text(data)}], "isError": False}
    except ToolError as exc:
        return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    except Exception:
        log.exception("MCP tool %s failed", name)
        return {"content": [{"type": "text", "text": "Error interno al ejecutar la herramienta"}], "isError": True}


async def _dispatch(ctx: Ctx, msg: dict) -> dict | None:
    method, rid = msg.get("method"), msg.get("id")
    params = msg.get("params") or {}
    if "method" not in msg or not isinstance(method, str) or not isinstance(params, dict):
        return _error(rid, -32600, "Mensaje JSON-RPC no válido") if "id" in msg else None
    if rid is None and "id" not in msg:
        return None
    if method == "initialize":
        asked = params.get("protocolVersion")
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": asked if asked in PROTOCOLS else PROTOCOLS[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "homehq", "version": "1.0"}, "instructions": INSTRUCTIONS}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": [t.listing() for t in TOOLS.values() if t.read_only or ctx.scope == "full"]}}
    if method == "tools/call":
        try:
            return {"jsonrpc": "2.0", "id": rid, "result": await _call(ctx, params)}
        except ValueError as exc:
            return _error(rid, -32602, str(exc))
    return _error(rid, -32601, f"Método no soportado: {method}")


@router.post("/mcp")
async def mcp_endpoint(request: Request, _user=Depends(mcp_token_user), db: Session = Depends(get_db)):
    db.close()
    if not _origin_ok(request):
        return JSONResponse(_error(None, -32600, "Origin no permitido"), status_code=403)
    body = await request.body()
    if len(body) > MAX_BODY:
        return JSONResponse(_error(None, -32600, "Mensaje demasiado grande"), status_code=413)
    try:
        payload = json.loads(body)
    except ValueError:
        return JSONResponse(_error(None, -32700, "JSON no válido"), status_code=400)
    ctx = Ctx(request.app, request.headers["authorization"], request.state.api_token.scope)
    if isinstance(payload, list):
        if not payload or len(payload) > 20 or not all(isinstance(m, dict) for m in payload):
            return JSONResponse(_error(None, -32600, "Lote no válido"), status_code=400)
        out = [r for r in [await _dispatch(ctx, m) for m in payload] if r]
        return JSONResponse(out) if out else Response(status_code=202)
    if not isinstance(payload, dict):
        return JSONResponse(_error(None, -32600, "Mensaje JSON-RPC no válido"), status_code=400)
    result = await _dispatch(ctx, payload)
    return JSONResponse(result) if result else Response(status_code=202)


@router.get("/mcp")
@router.delete("/mcp")
async def mcp_no_stream():
    return Response(status_code=405, headers={"Allow": "POST"})
