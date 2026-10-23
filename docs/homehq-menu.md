# Home HQ: weekly menu

The **Menú** screen shows what is for breakfast, lunch and dinner (and optionally mid-morning and afternoon snack) for
the whole week, like the paper menu on the fridge. Today's column is highlighted, so a glance is enough.

## How the rotation works

You can plan one week or several (up to 12). The weeks repeat in order, and you tell Home HQ which one is the current
week. Example: you plan weeks 1, 2 and 3 and say that this week is week 2. Next Monday the frame shows week 3, then
week 1, then week 2 again, and so on.

Internally `start_week` and `start_date` anchor the rotation: the week that contains `start_date` is `start_week`, and
every Monday after that moves one week forward, wrapping around after the last one. Setting the current week in the
panel simply rewrites those two values for today. Nothing needs a nightly job: the frame receives the whole rotation
and works out the week itself, using the same arithmetic as the backend (there is a test that keeps both in step).

## In the admin panel

Open **Menú semanal** in the side bar.

- Pick which meals are shown (breakfast, mid-morning, lunch, snack, dinner).
- Add, rename and remove weeks. Each week has seven day columns, Monday first.
- A **shared** row is for something that is the same all week (for instance "fruit" at mid-morning). It is written once
  and spans all seven columns on the frame.
- **Semana actual** sets which week is the current one ("Esta semana es la…" and **Aplicar**). The panel also shows when the next week starts.

The screen only appears in the frame's side rail once a menu has at least one week. It can be reordered like any other
screen under **Pantallas**, and it can be a frame's start view.

## For agents

The same data is available through [MCP](homehq-mcp.md): `get_menu`, `set_menu`, `set_menu_week`, `set_menu_day`,
`delete_menu_week` and `set_current_menu_week`. Changing one cell is a single call to `set_menu_day`.

REST, if you prefer it: `GET` and `PUT /api/v1/admin/menu`, `POST /api/v1/admin/menu/current-week`.
