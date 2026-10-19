# Home HQ: Home Assistant and the Amazon shopping list

Home Assistant (HA) is reached **only by the backend**, over its REST and WebSocket APIs. The token is stored
encrypted and is never sent to a frame or returned by the admin API.

## Connect

1. In HA create a long-lived access token (Profile > Security).
2. Admin panel > *Home Assistant*: enter the URL (`http://homeassistant.local:8123`), save the token
   (write-only field), press *Probar conexión*. Turn off *verify TLS* only for a self-signed certificate on your LAN.
3. Pick the entities the frames may see and control (*authorized entities*). Entities of these domains can be listed:
   `light`, `switch`, `climate`, `sensor`, `binary_sensor`, `scene`, `script`, `todo`, `person`. Frames can
   *control* only `light` (on, off, toggle, brightness), `switch`, `scene`, `script` and `climate` (temperature,
   HVAC mode). Anything not on the authorized list is invisible to frames, and the control endpoint rejects it.
4. For every frame choose the order of entities (*Pantalla principal*) and, optionally, presence sensors.

The backend keeps one WebSocket subscribed to `state_changed`, reconnects with exponential backoff (1 s to 60 s,
with jitter) and publishes the changes to the frames over SSE. When HA is down the dashboard shows the last
known state with a warning ("Sin conexión con Home Assistant") and the controls are disabled: it never pretends
to be live. Controls call HA through `POST /api/v1/device/ha/service`, which checks the entity against the
authorized list and the allowed services of its domain.

## Blinds, scenes and customisation

- **Blinds and curtains** (`cover.*`) can be authorised like lights. The frame shows raise / stop / lower buttons and, when
  the entity reports its position, a slider. The allowed services are `open_cover`, `close_cover`, `stop_cover`, `toggle`
  and `set_cover_position` (0 to 100).
- **Scenes and scripts** are shown as large tiles. For every authorised entity the admin panel (*Home Assistant*) lets you
  set another name, icon and colour for the frame; the Home Assistant entity itself is not modified.
- **Cameras** (`camera.*`) are not tiles in *Casa*; add them in *Cámaras* (see [homehq-chores-cameras.md](homehq-chores-cameras.md)).

## People and presence

People are the colours and owners of calendar events and the people chores are assigned to. A Home Assistant account is
not needed: linking a person to an HA `person.*` entity is optional and only adds *en casa / fuera*. Link each person to an HA `person.*` entity to show *en casa / fuera*. Real HA presence has the highest
priority when deciding whether the screen may sleep (see [light-sensor.md](light-sensor.md)).

## Amazon Alexa shopping list

Home HQ does not talk to Amazon. It uses the `todo.*` entity that HA exposes for the list.

1. Install the **Alexa Devices** integration in HA (core, recent versions) and sign in with your Amazon account.
   Availability depends on your region and Amazon account; check that HA shows a `todo.*` entity for the shopping
   list before relying on it. Alternatively use the "Alexa Media Player" community integration or any other
   `todo` platform (Todoist, Google Tasks, local To-do).
2. Authorize that `todo.*` entity in *Home Assistant*.
3. Admin panel > *Compra*: choose provider *Home Assistant* and select the entity.

If HA is unreachable the frames keep working: the shopping list is shown from cache and every change is queued
on the frame, then sent when the connection returns. The local provider is always available as a fallback
(*Compra > Local*). Conflict policy: [shopping.md](shopping.md).

> Verification status: the HA client, authorization, WebSocket reconnection and the shopping provider are covered by
> automated tests against a mock HA server. They have not been run against a real HA installation or against a real
> Amazon account in this repository.
