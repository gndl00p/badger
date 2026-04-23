try:
    import badger2040
except ImportError:
    badger2040 = None

import time

from fetcher import fetch
from render import render
from store import load as load_state
from store import save as save_state


_POLL_INTERVAL = 0.05


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
    render(display, data if data is not None else last, marker)
    if data is not None and marker is None:
        save_state(state_path, {"station_index": station_index, "last_data": data})


def run(state_path="/state.json"):
    display = _build_display()
    cfg = _load_config()
    stations = _stations(cfg)

    state = load_state(state_path)
    raw_idx = state.get("station_index")
    try:
        station_index = int(raw_idx) % len(stations) if raw_idx is not None else 0
    except (TypeError, ValueError):
        station_index = 0

    _cycle(display, cfg, state_path, station_index)

    refresh_s = getattr(cfg, "REFRESH_MINUTES", 15) * 60
    last_tick = time.time()
    while True:
        if _pressed(display, "BUTTON_A"):
            _cycle(display, cfg, state_path, station_index)
            last_tick = time.time()
            _wait_release(display, "BUTTON_A")
            continue
        if _pressed(display, "BUTTON_B"):
            station_index = (station_index - 1) % len(stations)
            _cycle(display, cfg, state_path, station_index)
            last_tick = time.time()
            _wait_release(display, "BUTTON_B")
            continue
        if _pressed(display, "BUTTON_C"):
            station_index = (station_index + 1) % len(stations)
            _cycle(display, cfg, state_path, station_index)
            last_tick = time.time()
            _wait_release(display, "BUTTON_C")
            continue
        if time.time() - last_tick >= refresh_s:
            _cycle(display, cfg, state_path, station_index)
            last_tick = time.time()
        time.sleep(_POLL_INTERVAL)


if __name__ == "__main__":
    run()
