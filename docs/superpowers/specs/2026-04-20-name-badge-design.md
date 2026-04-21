# Badger 2040 W — Dual-Mode Name Badge + Desk Info Display

**Date:** 2026-04-20
**Owner:** Philip Robb (philip@teamrobb.com)
**Hardware:** Pimoroni Badger 2040 W (RP2040 + Pico W + 296×128 1-bit e-ink + 5 front buttons + UP/DOWN + LiPo JST)

## Summary

A single Badger 2040 W unit that serves two modes:

1. **Badge mode** — portable conference/meeting name badge, battery-powered, Wi-Fi off, multi-screen deck navigated by buttons.
2. **Desk mode** — USB-powered desktop info display, Wi-Fi on, periodic refresh, single dashboard screen aggregating weather, next calendar event, Zoho Desk ticket queue, and Zoho CRM tasks due today.

Mode is persisted to on-device flash and toggled by a long-press on the B button. On boot the badge restores its previous mode.

## Goals

- Printable name-badge identity for Philip Robb, Technical Lead, Robb.Tech.
- Useful ambient desk dashboard when not being worn.
- No backend coupling on the device itself — device pulls one JSON blob from a local aggregator service running on the workstation (`endevour.robb.tech`).
- Low-maintenance: firmware lives in a git repo and is flashed from the workstation.

## Non-Goals

- Full interactive terminal / shell on the badge.
- Writing to Zoho from the badge.
- Acting as an llamaBot client.
- Supporting Badgers other than the 2040 W.

## Hardware

- **Board:** Badger 2040 W (Pico W, 2.4 GHz Wi-Fi, JST-PH LiPo connector, USB-C).
- **Display:** 296×128 monochrome e-ink, 1-bit, full-refresh only.
- **Input:** A, B, C (front), UP, DOWN (side).
- **Power:** USB-C in desk mode; LiPo (≥ 400 mAh recommended) in badge mode.
- **Storage:** 2 MB flash, small FAT filesystem for assets and `state.json`.

## Firmware

- **Runtime:** Pimoroni MicroPython build for Badger 2040 W (most recent stable release at implementation time).
- **Libraries used:** `badger2040w`, `jpegdec`, `qrcode`, `network`, `urequests`, `ujson`, `machine`.
- **Entry point:** `main.py` reads `state.json`, dispatches to the active mode module, and handles the mode-toggle long-press.

### Modes

#### Badge mode

- Wi-Fi is disabled.
- 5 screens, navigated with buttons:

  | Screen         | Content                                                                   |
  | -------------- | ------------------------------------------------------------------------- |
  | 1 — Name card  | Dithered headshot (128×128) left, "Philip Robb" / "Technical Lead" / "Robb.Tech" right, small QR (≈ 64×64) for `https://robb.tech`. |
  | 2 — Contact    | Whatever fields are populated in `CONTACT` (e.g. email, LinkedIn, website). Each with a small QR.        |
  | 3 — Bio        | 1–2 sentence bio + skill keywords.                                        |
  | 4 — Now        | "What Philip is working on" — static text, edited in `config.py`.         |
  | 5 — Logo       | Robb.Tech wordmark centered, full bleed.                                  |

- Button bindings:

  | Button | Action                                         |
  | ------ | ---------------------------------------------- |
  | A      | Previous screen                                |
  | C      | Next screen                                    |
  | B      | Redraw current screen                          |
  | B long | Toggle mode → Desk                             |
  | UP     | Toggle backlight (LED on/off)                  |
  | DOWN   | `halt()` — deep sleep, wake on any button      |

- After rendering, the device calls `badger2040w.halt()` to cut power until the next button press. This is the power model that lets the badge run for days on a 400 mAh LiPo.

#### Desk mode

- Wi-Fi connects on boot using credentials from `config.py`.
- Device fetches `http://endevour.robb.tech:8088/badge.json` every 15 min (`machine.deepsleep(15*60*1000)` between refreshes; USB supplies wake power).
- Single dashboard screen, four tiles laid out on the 296×128 display:

  ```
  ┌──────────────────────────┬──────────────────────────┐
  │ Mon 20 Apr · 72°F sunny  │ Next: 3:00p Standup      │
  ├──────────────────────────┼──────────────────────────┤
  │ Desk: 4 tickets open     │ CRM: 2 tasks due today   │
  └──────────────────────────┴──────────────────────────┘
  ```

- Failure modes:
  - Wi-Fi connect failure → render last-known dashboard from `state.json` with a small "stale" marker and timestamp.
  - HTTP fetch failure → same, but marker says "offline".
  - Parse failure → same, marker says "bad payload".

- Button bindings:

  | Button | Action                                         |
  | ------ | ---------------------------------------------- |
  | A      | Force refresh now                              |
  | B long | Toggle mode → Badge                            |
  | C      | No-op (reserved)                               |
  | UP     | Toggle backlight                               |
  | DOWN   | `halt()`                                       |

### Mode switching

- Long-press B = ≥ 2 s.
- On release, write the new mode into `state.json` (`{"mode": "badge"|"desk", "last_data": {...}}`), render a short "switching to <mode>…" confirmation, then soft-reset so the mode module starts from a clean slate.

## Aggregator service (endevour)

- **Purpose:** keep the badge dumb. All upstream API calls, token handling, and error smoothing happen on the workstation, which already has network, secrets, and MCP servers configured.
- **Process:** `~/code/badger/server/app.py`, served by `uvicorn` on `127.0.0.1:8088`, fronted on the LAN by the workstation's existing reverse proxy (already in place for other tools).
- **Endpoint:** `GET /badge.json`
- **Auth:** LAN-only; token shared header (`X-Badge-Token`) matched against `BADGE_TOKEN` env var. Badge includes the same token from `config.py`.
- **Response shape:**

  ```json
  {
    "generated_at": "2026-04-20T22:45:00-05:00",
    "weather": { "temp_f": 72, "summary": "sunny", "icon": "sun" },
    "calendar": { "next": { "start": "2026-04-20T15:00:00-05:00", "title": "Standup" } },
    "desk":     { "open_tickets": 4 },
    "crm":      { "tasks_due_today": 2 }
  }
  ```

- **Upstream integrations:**
  - Weather: `open-meteo.com` (no key), fixed lat/long for home/office.
  - Calendar: Google Calendar API via service account JSON on workstation. Returns next upcoming event within the next 24 h.
  - Zoho Desk: existing ZohoDesk OAuth creds, `getOpenRequestsCount` or `getTicketQueueViewCount`.
  - Zoho CRM: existing ZohoCRM OAuth creds, COQL query for open Tasks where `Due_Date == today` and `Owner == current user`.
- **Caching:** each upstream is fetched with a small in-process cache (60 s weather, 60 s calendar, 30 s Zoho). The endpoint never blocks > 2 s; on upstream timeout, it returns the last successful value and sets a per-tile `"stale": true` flag.
- **Deployment:** `~/code/badger/server/badger.service` is a user systemd unit, same pattern as `tgbot.service`. Enabled with `systemctl --user enable --now badger`.

## Configuration

`config.py` on the device (not checked in as-is; repo ships `config.example.py`):

```python
NAME = "Philip Robb"
TITLE = "Technical Lead"
ORG = "Robb.Tech"
URL = "https://robb.tech"
CONTACT = {
    "email": "philip@teamrobb.com",
    "linkedin": "https://www.linkedin.com/in/…",
}
BIO = "…"
NOW = "Building out the Robb.Tech platform."

WIFI_SSID = "…"
WIFI_PSK = "…"

AGGREGATOR_URL = "http://endevour.robb.tech:8088/badge.json"
AGGREGATOR_TOKEN = "…"
REFRESH_MINUTES = 15
```

## Repo layout

```
~/code/badger/
├── README.md
├── main.py
├── config.example.py
├── state.json                # written at runtime; repo ships empty {}
├── modes/
│   ├── __init__.py
│   ├── badge.py
│   └── desk.py
├── screens/                  # badge-mode screens
│   ├── __init__.py
│   ├── name_card.py
│   ├── contact.py
│   ├── bio.py
│   ├── now.py
│   └── logo.py
├── assets/
│   ├── headshot.bin          # 128×128 1-bit, converted from source image
│   └── robbtech_wordmark.bin
├── tools/
│   ├── dither_image.py       # host-side tool: JPG/PNG → 1-bit .bin
│   └── flash.sh              # wraps mpremote / picotool
├── server/
│   ├── app.py
│   ├── requirements.txt
│   ├── badger.service
│   └── .env.example
└── docs/superpowers/specs/2026-04-20-name-badge-design.md
```

## Power model

- **Badge mode:** ~fraction of a second of draw current during a refresh (~50 mA peak, ~2–3 s for full refresh), then `halt()`. Idle current in `halt()` is ≤ 10 µA. A 400 mAh LiPo easily covers multiple days of conference use at dozens of refreshes per day.
- **Desk mode:** USB supplies power; `deepsleep` between refreshes keeps Wi-Fi off most of the time. Assume a full refresh uses ≤ 50 mJ; negligible at USB power.

## Testing

- **Host-side (no device):**
  - `tools/dither_image.py` has a pytest that round-trips a fixture image and asserts the output dimensions + bit depth.
  - `server/app.py` has pytest coverage for:
    - Token-gating on `/badge.json`.
    - Each upstream integration stubbed with recorded fixtures.
    - Stale-data fallback when an upstream is monkeypatched to raise.
- **On-device (manual, one-off):**
  - Flash firmware, long-press B, confirm the mode toggle renders and persists across a reset.
  - Verify aggregator fetch by toggling Wi-Fi off on the workstation and confirming the badge shows the `"offline"` marker with the last-known dashboard.
  - Leave in badge mode on battery overnight; verify still responsive the next morning.

## Open questions / assumptions

- Assumed Wi-Fi credentials for your desk network will be added to `config.py` manually at flash time.
- Assumed the existing ZohoDesk and ZohoCRM OAuth credentials on the workstation (used by the MCP servers) are reusable from the aggregator service. If they are namespaced per-tool, the aggregator will need its own OAuth client.
- Aggregator port `8088` is assumed free on the workstation; if not, will bump.
- Headshot source: expecting a ≥ 600×600 PNG/JPG from Philip before the main-card screen can be finalised. Until that exists, the name-card screen renders with a placeholder silhouette.
