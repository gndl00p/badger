# Changelog

## [0.3.0] — 2026-04-26

Visual redesign + a stack of new aviation features.

### Added
- **Density altitude (DA)** + **pressure altitude (PA)** computed from
  the current METAR temp + altimeter setting + station field elevation.
- **Altimeter setting (inHg)** rendered on the main view alongside DA.
- **Dewpoint (°F)** + **temp/dew spread**.
- **Sunrise / sunset** computed from the station's lat/lon and the
  observation date (NOAA-ish solar formula). New `TIMEZONE_OFFSET`
  config field controls the local-time conversion.
- **Crosswind / headwind component** for an optional per-station primary
  runway via the new `RUNWAYS = {"KLBB": 170, ...}` config dict.
- **TAF view** — third B-press from the main screen fetches and renders
  the current Terminal Aerodrome Forecast for the selected station.
- **Status page** (button **C**) — battery voltage with auto USB / LiPo
  label, Wi-Fi signal + IP or `offline`, current station, last
  observation time.
- **Picker** (UP / DOWN) for cycling between configured stations.
- **Auto-cycle stations** — `AUTO_CYCLE_MINUTES` config rotates the
  displayed station on its own clock.
- **Boot splash** — "SkyGlance / aviation weather" frame on power-up.
- **LED heartbeat** — 80 ms pulse every 20 s confirming firmware is live.
- **Multi-station support** — `METAR_STATIONS = [...]` list, persisted
  per-device selection in `state.json`.
- **Inverted flight-category block** — the big `IFR` / `LIFR` indicator
  renders white-on-black for instant emergency signal.
- **Dark mode overnight** — full panel inverts between 22:00 – 06:00
  local; honours `TIMEZONE_OFFSET`.
- **Retry with backoff** — failed fetches retry on 30 / 60 / 120 / 300 s
  schedule, capped by `REFRESH_MINUTES`.
- **Battery-aware refresh** — on LiPo, the refresh interval stretches
  to ≥ 30 min to be gentler on the cell.
- Repository hero photo (`badger.jpg`) on the README.

### Changed
- **Main display redesign**: three-zone layout — small header strip
  (station + city + observation Zulu time), big hero (temp + flight
  category), labelled body grid (`KLBB · 10SM · DA5800` / wind +
  temp/dew / clouds) with a small bottom strip for runway and
  sunrise/sunset.
- **Body rows bumped to scale 2** so they're readable at desk distance.
- Aggregator-style `payload.weather.*` envelope removed; weather is a
  flat dict.
- Ceiling, dewpoint, altimeter, lat/lon, runway components, and station
  name added to the parsed weather dict.

### Fixed
- `_short_name` now hand-rolls title-case — MicroPython's `str` does
  not implement `.capitalize()`, which was silently swallowing the
  airport-info parse and leaving DA blank.
- `_station_info` retries once with `gc.collect()` between attempts;
  Pico W's TLS stack often fails the second back-to-back HTTPS call.
- Night-mode flag is now recomputed from observation UTC + current
  `TIMEZONE_OFFSET` every cycle, not pulled from the saved state, so
  config edits take effect immediately.
- Cloud-row dither bit polarity reverted to bit=1-for-black to match
  Pimoroni's `picographics.image()` convention (no longer used now that
  the dither tool is gone, but the convention is documented in
  troubleshooting).
- Various MicroPython incompatibilities (dict-spread `{**x, ...}` →
  `dict.copy()`, `state` filename collision with the Pimoroni factory
  `state/` directory).

## [0.2.0] — 2026-04-23

Major pivot: SkyGlance is now a single-purpose aviation weather display.

### Removed
- **Badge mode**: all five name-card screens, mode-switch detector,
  placeholder-asset generator, dither tool, asset files. The device is
  no longer a dual-mode badge.
- **FastAPI aggregator**: `server/` directory removed in full. The
  device calls `aviationweather.gov` directly over HTTPS — no server,
  no API key, no shared secret.
- **Zoho Desk / Zoho CRM / Google Calendar upstreams**: no longer part
  of the project.
- `tools/dither_image.py`, `tools/make_placeholder_assets.py`, and
  `assets/*.bin`.

### Changed
- Project renamed **badger** → **SkyGlance**.
- Firmware tree flattened: no more `modes/`, `screens/`, `desk/`
  subdirectories — just `main.py`, `fetcher.py`, `render.py`,
  `store.py` at the repository root.
- `badge_state.py` renamed to `store.py`; state.json now stores just
  `{"last_data": {...}}` (no mode field).
- Weather payload is now a flat dict (no `payload.weather.*` nesting)
  since the aggregator envelope is gone.
- Observation time is rendered with a `Z` suffix to flag UTC.
- `tools/flash.sh` trimmed to four firmware files plus `config.py`.
- `config.example.py` reduced to four fields: `WIFI_SSID`, `WIFI_PSK`,
  `METAR_STATION`, `REFRESH_MINUTES`.
- `pyproject.toml` `name` bumped to `skyglance`, version `0.2.0`.

### Added
- `fetcher.py` now contains the full METAR parser (ported from the
  retired aggregator's `weather.py`).
- Host test suite trimmed to the four firmware modules; 24 tests cover
  fetcher / render / store / main.

### Fixed
- Swapped `{**dict, "stale": True}` spread (not supported by some
  MicroPython builds) for an explicit `_stale_copy` helper.

## [0.1.0] — 2026-04-20

Initial release under the `badger` name — dual-mode firmware (badge
+ desk), FastAPI aggregator, per-tile stale fallback, 84 tests.

[0.3.0]: https://github.com/gndl00p/skyglance/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/gndl00p/skyglance/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/gndl00p/skyglance/releases/tag/v0.1.0
