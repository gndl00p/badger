try:
    import badger2040
except ImportError:
    badger2040 = None

import time

from fetcher import fetch, fetch_taf
from render import render as render_weather
from picker import render as render_picker
from status import render as render_status
from raw import render as render_raw
from splash import render as render_splash
from taf import render as render_taf
from status import _battery_v
from store import load as load_state
from store import save as save_state


_POLL_INTERVAL = 0.05

_UPDATE_NORMAL = 0
_UPDATE_TURBO = 3

# Backoff schedule (seconds) when consecutive fetches fail. Capped by the
# configured REFRESH_MINUTES baseline.
_BACKOFF_SECONDS = (30, 60, 120, 300)

# Battery voltage below this is treated as running on LiPo, not USB.
_USB_THRESHOLD_V = 4.5

_HEARTBEAT_INTERVAL_S = 20.0
_HEARTBEAT_DURATION_S = 0.08
_HEARTBEAT_BRIGHTNESS = 60


def _set_speed(display, speed):
    try:
        display.set_update_speed(speed)
    except Exception:
        pass


class Heartbeat:
    """Periodic LED blink so the owner can see the firmware is still alive."""

    def __init__(self, interval=_HEARTBEAT_INTERVAL_S, duration=_HEARTBEAT_DURATION_S,
                 brightness=_HEARTBEAT_BRIGHTNESS):
        self.interval = interval
        self.duration = duration
        self.brightness = brightness
        self.last = 0.0
        self.on_until = 0.0
        self.on = False

    def tick(self, display, now):
        if self.on:
            if now >= self.on_until:
                try:
                    display.led(0)
                except Exception:
                    pass
                self.on = False
            return
        if now - self.last >= self.interval:
            try:
                display.led(self.brightness)
            except Exception:
                pass
            self.on = True
            self.on_until = now + self.duration
            self.last = now


def _stations(cfg):
    stations = getattr(cfg, "METAR_STATIONS", None)
    if stations:
        return list(stations)
    single = getattr(cfg, "METAR_STATION", "KLBB")
    return [single]


def _pressed(display, attr):
    if badger2040 is None:
        return False
    btn = getattr(badger2040, attr, None)
    if btn is None:
        return False
    return display.pressed(btn)


def _wait_release(display, attr):
    if badger2040 is None:
        return
    btn = getattr(badger2040, attr, None)
    if btn is None:
        return
    while display.pressed(btn):
        time.sleep(_POLL_INTERVAL)


def _build_display():
    return badger2040.Badger2040()


def _load_config():
    import config
    return config


def _cycle(display, cfg, state_path, station_index):
    stations = _stations(cfg)
    station = stations[station_index % len(stations)]
    state = load_state(state_path)
    last = state.get("last_data")
    data, marker = fetch(cfg, last, station=station)
    render_weather(display, data if data is not None else last, marker)
    if data is not None and marker is None:
        save_state(state_path, {"station_index": station_index, "last_data": data})
    return marker


def _refresh_interval_s(cfg):
    base = getattr(cfg, "REFRESH_MINUTES", 15) * 60
    v = _battery_v()
    if v is not None and v < _USB_THRESHOLD_V:
        # On battery — at least 30 min between refreshes.
        base = max(base, 30 * 60)
    return base


def _next_delay_s(cfg, consecutive_failures):
    if consecutive_failures <= 0:
        return _refresh_interval_s(cfg)
    idx = min(consecutive_failures - 1, len(_BACKOFF_SECONDS) - 1)
    # Never wait longer between retries than a normal refresh would take.
    return min(_BACKOFF_SECONDS[idx], _refresh_interval_s(cfg))


def run(state_path="/state.json"):
    display = _build_display()
    cfg = _load_config()
    stations = _stations(cfg)

    render_splash(display)

    state = load_state(state_path)
    raw_idx = state.get("station_index")
    try:
        station_index = int(raw_idx) % len(stations) if raw_idx is not None else 0
    except (TypeError, ValueError):
        station_index = 0

    initial_marker = _cycle(display, cfg, state_path, station_index)

    last_tick = time.time()
    view = "main"
    cursor = station_index
    heartbeat = Heartbeat()
    consecutive_failures = 0 if initial_marker is None else 1
    auto_cycle_s = getattr(cfg, "AUTO_CYCLE_MINUTES", 0) * 60
    last_auto_cycle = time.time()

    while True:
        heartbeat.tick(display, time.time())

        if view == "main":
            if _pressed(display, "BUTTON_A"):
                marker = _cycle(display, cfg, state_path, station_index)
                consecutive_failures = 0 if marker is None else consecutive_failures + 1
                last_tick = time.time()
                _wait_release(display, "BUTTON_A")
            elif _pressed(display, "BUTTON_B"):
                view = "raw"
                saved = load_state(state_path).get("last_data") or {}
                render_raw(display, saved)
                _wait_release(display, "BUTTON_B")
            elif _pressed(display, "BUTTON_C"):
                view = "status"
                current_station = stations[station_index]
                saved = load_state(state_path).get("last_data") or {}
                render_status(display, current_station, saved.get("updated_z"))
                _wait_release(display, "BUTTON_C")
            elif _pressed(display, "BUTTON_UP") or _pressed(display, "BUTTON_DOWN"):
                cursor = station_index
                view = "list"
                # First menu frame gets a clean NORMAL refresh so ghosting
                # from the weather view doesn't bleed into the list.
                _set_speed(display, _UPDATE_NORMAL)
                render_picker(display, stations, cursor, station_index)
                for attr in ("BUTTON_UP", "BUTTON_DOWN"):
                    _wait_release(display, attr)
            else:
                now = time.time()
                # Auto-cycle station rotation takes precedence when enabled.
                if auto_cycle_s > 0 and now - last_auto_cycle >= auto_cycle_s:
                    station_index = (station_index + 1) % len(stations)
                    marker = _cycle(display, cfg, state_path, station_index)
                    consecutive_failures = 0 if marker is None else consecutive_failures + 1
                    last_auto_cycle = now
                    last_tick = now
                elif now - last_tick >= _next_delay_s(cfg, consecutive_failures):
                    marker = _cycle(display, cfg, state_path, station_index)
                    consecutive_failures = 0 if marker is None else consecutive_failures + 1
                    last_tick = now
        elif view == "list":
            if _pressed(display, "BUTTON_UP"):
                cursor = (cursor - 1) % len(stations)
                # Subsequent moves use TURBO — ghosting acceptable, speed matters.
                _set_speed(display, _UPDATE_TURBO)
                render_picker(display, stations, cursor, station_index)
                _wait_release(display, "BUTTON_UP")
            elif _pressed(display, "BUTTON_DOWN"):
                cursor = (cursor + 1) % len(stations)
                _set_speed(display, _UPDATE_TURBO)
                render_picker(display, stations, cursor, station_index)
                _wait_release(display, "BUTTON_DOWN")
            elif _pressed(display, "BUTTON_A"):
                station_index = cursor
                view = "main"
                marker = _cycle(display, cfg, state_path, station_index)
                consecutive_failures = 0 if marker is None else consecutive_failures + 1
                last_tick = time.time()
                last_auto_cycle = time.time()
                _wait_release(display, "BUTTON_A")
            elif _pressed(display, "BUTTON_B"):
                view = "main"
                marker = _cycle(display, cfg, state_path, station_index)
                consecutive_failures = 0 if marker is None else consecutive_failures + 1
                _wait_release(display, "BUTTON_B")
        elif view == "status":
            if _pressed(display, "BUTTON_B"):
                view = "main"
                marker = _cycle(display, cfg, state_path, station_index)
                consecutive_failures = 0 if marker is None else consecutive_failures + 1
                last_tick = time.time()
                _wait_release(display, "BUTTON_B")
            elif _pressed(display, "BUTTON_A"):
                current_station = stations[station_index]
                saved = load_state(state_path).get("last_data") or {}
                render_status(display, current_station, saved.get("updated_z"))
                _wait_release(display, "BUTTON_A")
        elif view == "raw":
            if _pressed(display, "BUTTON_B"):
                # Second B press from the details page → TAF view.
                view = "taf"
                current_station = stations[station_index]
                raw_taf = fetch_taf(current_station)
                render_taf(display, raw_taf, station=current_station)
                _wait_release(display, "BUTTON_B")
        elif view == "taf":
            if _pressed(display, "BUTTON_B"):
                view = "main"
                marker = _cycle(display, cfg, state_path, station_index)
                consecutive_failures = 0 if marker is None else consecutive_failures + 1
                last_tick = time.time()
                _wait_release(display, "BUTTON_B")

        time.sleep(_POLL_INTERVAL)


if __name__ == "__main__":
    run()
