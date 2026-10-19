# Home HQ: pairing a frame

A frame can only read data or send commands after an administrator approves it. There is no anonymous access.

1. **Frame, step 1.** On first start the app shows "Conectar con Home HQ". Backends that the frame finds by
   mDNS are offered as buttons; otherwise type `ip:puerto` (for example `192.168.1.177:8787`).
   The manual address is always available.
2. **Frame, step 2.** The frame asks the backend for a pairing request and shows a six digit code.
   The request expires after 10 minutes (`HOMEHQ_PAIRING_TTL_SECONDS`).
3. **Admin panel.** Open `/admin/`, go to *Marcos*, pick the pending request, type the code shown on the
   frame and give the frame a name. The code is not displayed in the panel on purpose: typing it proves
   that you are standing next to the frame you are approving.
4. **Frame.** It receives its personal token (stored only in the app's private preferences), downloads its
   configuration and opens the dashboard. From then on it reconnects by itself.

Pairing and polling are rate limited per IP.

## Change, revoke, unpair

- *Marcos > frame > Eliminar* revokes the token immediately; the frame returns to the setup screen.
- To move a frame to another server, press and hold the button "Mantén pulsado para desvincular" in *Ajustes*
  on the frame for 1.5 s, then pair again.
- The two-finger long press (1.5 s) opens the maintenance menu (launcher, Android settings, Wi-Fi, reload).

## From the command line (testing)

```sh
curl -s -X POST http://SERVER:8787/api/v1/pairing/request -H 'Content-Type: application/json' \
  -d '{"name":"test","model":"curl"}'
```

then approve in the panel with the returned code. The admin API needs the `X-HomeHQ-Admin: 1` header on
every non-GET request.
