# Home HQ: shopping list and conflict policy

The list lives behind a `ShoppingProvider` in the backend:

| Provider | Storage | Use |
| --- | --- | --- |
| `local` | SQLite | Default and fallback. |
| `homeassistant` | any HA `todo.*` entity (Alexa lists, Todoist, ...) | Chosen in the admin panel, see [homehq-homeassistant.md](homehq-homeassistant.md). |

Operations: add, complete, reopen, delete and rename. On the frame, pending items are on top, completed ones are
separated below and a counter shows what is left.

## Offline queue

Each action on the frame gets a unique id, is applied optimistically and is stored in a persisted queue. When the
backend answers, the queue is drained in order. If the request fails (network, backend down) the queue is kept and
retried every 10 seconds; if the backend rejects an operation with a 4xx error, the queue is dropped so a bad
operation can never block the rest. After applying, the frame replaces its list with the authoritative one.

## Deterministic conflict policy

1. Every operation id is applied at most once. A replay returns the first result.
2. `add` never duplicates. A pending item with the same normalised name (case, accents and spaces ignored) is reused;
   a completed one is reopened.
3. `set_done` is an absolute state, not a toggle. The last write, in arrival order at the backend, wins.
4. `remove` wins. Any later operation on a removed item is a harmless no-op.

Two frames that edit the same list therefore converge to the same result regardless of retries.
