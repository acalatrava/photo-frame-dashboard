# Home HQ: MCP for agents

Home HQ speaks the [Model Context Protocol](https://modelcontextprotocol.io), so an AI agent (Cursor, Claude, a script)
can configure the frames, the menu, the calendars, the photos and the rest, without touching the panel.

- Endpoint: `POST http://<server>:8787/mcp` (Streamable HTTP, JSON-RPC 2.0, stateless, no streaming).
- Authentication: `Authorization: Bearer hqa_...`, an **API token** created in the panel under **Agentes (MCP)**.

## 1. Create a token

In the panel, open **Agentes (MCP)** and create a token. Choose:

| Scope | What the agent can do |
| --- | --- |
| `read` | Only see things: status, configuration, devices, menu, albums. Write tools are not even listed. |
| `full` | Everything in the list below. |

You can also set an expiry. The token is shown **once**; only its SHA-256 and its first characters are stored, so it
cannot be recovered. Revoke it from the same page at any time. There is a maximum of 20 active tokens.

## 2. Connect a client

Cursor (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "homehq": {
      "url": "http://192.168.1.177:8787/mcp",
      "headers": { "Authorization": "Bearer hqa_xxxxxxxx" }
    }
  }
}
```

Quick check from a shell:

```sh
curl -s http://192.168.1.177:8787/mcp -H "Authorization: Bearer $HQ_TOKEN" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## 3. What it can do

Reading (all scopes): `get_status`, `get_config`, `get_config_schema`, `list_devices`, `get_device`,
`list_pairing_requests`, `get_device_telemetry`, `get_menu`, `list_homeassistant_entities`, `list_frigate_cameras`,
`list_albums`, `list_photos`, `list_app_updates`.

Writing (`full` only):

- Configuration: `update_config` takes a *merge patch* (send only what changes; `null` removes a key) and is validated
  against the same schema as the panel. `upsert_collection_item` and `delete_collection_item` edit lists such as
  people, calendars, chores, cameras and entities by their id, without resending the whole list.
- Frames: `update_device`, `send_device_command`, `revoke_device`, `approve_pairing`, `reject_pairing`.
- Menu: `set_menu`, `set_menu_week`, `set_menu_day`, `delete_menu_week`, `set_current_menu_week`
  (see [homehq-menu.md](homehq-menu.md)).
- Integrations: `sync_calendar`, `set_calendar_password`, `set_homeassistant_token`, `test_homeassistant`.
- Photos: `create_album`, `rename_album`, `delete_album`, `set_photo_caption`, `delete_photo`.
- Updates: `set_update_mode`.

Start with `get_config_schema`: it tells the agent every field, its type and limits, so it can build a valid patch.
Secrets (Home Assistant token, calendar passwords) can be written but never read back.

Not available through MCP, on purpose: uploading photos (binary), and uploading, publishing or deleting frame APKs.

## 4. Security notes

- **A `full` token is nearly an admin password.** Anyone holding it can change the configuration of every frame, read
  the calendar and photo metadata and pair new frames. Give each agent its own token, prefer `read` when it only needs
  to look, set an expiry, and keep it out of repositories and chat logs.
- Things a token can never do, whatever its scope: create or revoke tokens, change the admin password, and upload,
  publish or delete the frame app. Those need a real logged-in panel session, because an APK installed on the frames is
  code that runs on them.
- Tokens are not the panel's JWT cookies. The panel keeps its 15 minute access token and rotating refresh token in
  `HttpOnly`, `Secure`, `SameSite=Strict` cookies. Agents cannot use cookies, so they use long-lived bearer tokens
  instead; the compensations are scope, expiry, revocation and the failed-attempt rate limit (30 wrong tokens per
  15 minutes per address).
- Run the server behind HTTPS if the agent is not on your LAN. A bearer token sent over plain HTTP can be read by
  anyone on the path. With a reverse proxy, set `HOMEHQ_TRUST_PROXY=true` and `HOMEHQ_TRUSTED_PROXY_HOPS` to the number
  of proxies, see [homehq-install.md](homehq-install.md).
- Browsers: requests with an `Origin` header that is neither the server itself nor in `HOMEHQ_CORS_ORIGINS` are refused, requests are capped at 1 MB and tool
  output at 60,000 characters.
