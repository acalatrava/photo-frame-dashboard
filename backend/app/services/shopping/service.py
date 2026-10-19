"""Shopping list with pluggable providers.

ShoppingProvider
    |- LocalShoppingProvider          (SQLite, always available)
    |- HomeAssistantShoppingProvider  (any todo.* entity, e.g. Amazon Alexa lists via Alexa Devices)

Conflict policy (deterministic, see docs/shopping.md):
  1. Every client operation has an id and is applied at most once (replays return the first result).
  2. `add` never duplicates: a pending item with the same normalised name is reused, a completed
     one with that name is re-opened.
  3. `set_done` is an absolute state, last write (in arrival order) wins.
  4. `remove` wins; any later operation on a removed item is a harmless no-op.
"""
import re
import secrets as pysecrets
import unicodedata
from typing import Protocol

from sqlalchemy.orm import Session

from ...core.db import session_scope
from ...models import ShoppingItem, ShoppingOpLog
from .. import config_service
from ..homeassistant.client import HAClient, HAError


def norm(name: str) -> str:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", n).strip()


class ProviderError(Exception):
    pass


class ShoppingProvider(Protocol):
    name: str

    async def list_items(self) -> list[dict]: ...
    async def add(self, name: str, note: str = "") -> dict: ...
    async def set_done(self, item_id: str, done: bool) -> bool: ...
    async def remove(self, item_id: str) -> bool: ...
    async def rename(self, item_id: str, name: str) -> bool: ...


class LocalShoppingProvider:
    name = "local"

    async def list_items(self) -> list[dict]:
        with session_scope() as db:
            rows = db.query(ShoppingItem).order_by(ShoppingItem.done, ShoppingItem.position, ShoppingItem.created_at).all()
            return [self._d(r) for r in rows]

    @staticmethod
    def _d(r: ShoppingItem) -> dict:
        return {"id": r.id, "name": r.name, "note": r.note, "done": r.done, "quantity": r.quantity,
                "position": r.position}

    async def add(self, name: str, note: str = "") -> dict:
        n = norm(name)
        with session_scope() as db:
            existing = db.query(ShoppingItem).filter(ShoppingItem.norm_name == n) \
                .order_by(ShoppingItem.done).first()
            if existing:
                existing.done = False
                return {**self._d(existing), "deduped": True}
            pos = (db.query(ShoppingItem).count() or 0) + 1
            row = ShoppingItem(id=pysecrets.token_hex(6), name=name.strip(), norm_name=n, note=note, position=pos)
            db.add(row)
            db.flush()
            return {**self._d(row), "deduped": False}

    async def set_done(self, item_id: str, done: bool) -> bool:
        with session_scope() as db:
            row = db.get(ShoppingItem, item_id)
            if not row:
                return False
            row.done = done
            return True

    async def remove(self, item_id: str) -> bool:
        with session_scope() as db:
            row = db.get(ShoppingItem, item_id)
            if not row:
                return False
            db.delete(row)
            return True

    async def rename(self, item_id: str, name: str) -> bool:
        with session_scope() as db:
            row = db.get(ShoppingItem, item_id)
            if not row:
                return False
            row.name, row.norm_name = name.strip(), norm(name)
            return True


class HomeAssistantShoppingProvider:
    name = "homeassistant"

    def __init__(self, ha: HAClient, entity_id: str):
        self.ha, self.entity = ha, entity_id

    async def _items(self) -> list[dict]:
        try:
            res = await self.ha.call_service("todo", "get_items", {"entity_id": self.entity}, return_response=True)
        except HAError as exc:
            raise ProviderError(str(exc)) from exc
        sr = (res or {}).get("service_response", {})
        return sr.get(self.entity, {}).get("items", [])

    async def list_items(self) -> list[dict]:
        items = await self._items()
        return [{"id": i.get("uid") or i["summary"], "name": i["summary"], "note": i.get("description") or "",
                 "done": i.get("status") == "completed", "quantity": 1, "position": idx}
                for idx, i in enumerate(items)]

    async def _call(self, service: str, data: dict) -> None:
        try:
            await self.ha.call_service("todo", service, {"entity_id": self.entity, **data})
        except HAError as exc:
            raise ProviderError(str(exc)) from exc

    async def add(self, name: str, note: str = "") -> dict:
        n = norm(name)
        for it in await self.list_items():
            if norm(it["name"]) == n:
                if it["done"]:
                    await self._call("update_item", {"item": it["id"], "status": "needs_action"})
                return {**it, "done": False, "deduped": True}
        data = {"item": name.strip()}
        if note:
            data["description"] = note
        await self._call("add_item", data)
        for it in await self.list_items():
            if norm(it["name"]) == n:
                return {**it, "deduped": False}
        return {"id": name.strip(), "name": name.strip(), "note": note, "done": False, "quantity": 1,
                "position": 0, "deduped": False}

    async def _exists(self, item_id: str) -> bool:
        return any(i["id"] == item_id for i in await self.list_items())

    async def set_done(self, item_id: str, done: bool) -> bool:
        if not await self._exists(item_id):
            return False
        await self._call("update_item", {"item": item_id, "status": "completed" if done else "needs_action"})
        return True

    async def remove(self, item_id: str) -> bool:
        if not await self._exists(item_id):
            return False
        await self._call("remove_item", {"item": [item_id]})
        return True

    async def rename(self, item_id: str, name: str) -> bool:
        if not await self._exists(item_id):
            return False
        await self._call("update_item", {"item": item_id, "rename": name.strip()})
        return True


def get_provider(db: Session, ha: HAClient) -> ShoppingProvider:
    g, _ = config_service.get_global(db)
    if g.shopping.provider == "homeassistant" and g.shopping.ha_entity and g.homeassistant.enabled:
        return HomeAssistantShoppingProvider(ha, g.shopping.ha_entity)
    return LocalShoppingProvider()


async def apply_ops(provider: ShoppingProvider, ops: list[dict], device_id: str | None) -> list[dict]:
    """Apply a batch of client operations in order, idempotently. Returns one result per op."""
    results: list[dict] = []
    temp_ids: dict[str, str] = {}
    for op in ops:
        op_id = op["op_id"]
        with session_scope() as db:
            logged = db.get(ShoppingOpLog, op_id)
            prior = logged.result if logged else None
        if prior is not None:
            if prior.get("client_id") and prior.get("id"):
                temp_ids[prior["client_id"]] = prior["id"]
            results.append({**prior, "replayed": True})
            continue
        res = await _apply_one(provider, op, temp_ids)
        with session_scope() as db:
            db.merge(ShoppingOpLog(op_id=op_id, device_id=device_id, result=res))
        results.append(res)
    return results


async def _apply_one(provider: ShoppingProvider, op: dict, temp_ids: dict[str, str]) -> dict:
    kind = op["type"]
    target = temp_ids.get(op.get("id") or "", op.get("id"))
    if kind == "add":
        item = await provider.add(op["name"], op.get("note", ""))
        if op.get("client_id"):
            temp_ids[op["client_id"]] = item["id"]
        return {"op_id": op["op_id"], "ok": True, "id": item["id"], "client_id": op.get("client_id"),
                "deduped": item.get("deduped", False)}
    if not target:
        return {"op_id": op["op_id"], "ok": True, "noop": True}
    if kind == "set_done":
        found = await provider.set_done(target, bool(op["done"]))
    elif kind == "remove":
        found = await provider.remove(target)
    elif kind == "rename":
        found = await provider.rename(target, op["name"])
    else:
        return {"op_id": op["op_id"], "ok": False, "error": "unknown op"}
    return {"op_id": op["op_id"], "ok": True, "noop": not found}
