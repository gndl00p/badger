from types import SimpleNamespace

from tests.fakes.display import FakeDisplay

import main


def _cfg(stations=None):
    return SimpleNamespace(
        WIFI_SSID="n", WIFI_PSK="p",
        METAR_STATIONS=stations or ["KLBB", "KAUS"],
        REFRESH_MINUTES=15,
    )


def test_cycle_saves_on_fresh_fetch(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    p.write_text("{}")
    d = FakeDisplay()

    metar = {"temp_f": 72, "station": "KLBB", "flight_category": "VFR",
             "wind": "180 5kt", "summary": "CLR", "updated_z": "20:00",
             "visibility_sm": 10.0, "ceiling_ft": None, "raw": "",
             "stale": False}

    captured = {}

    def fake_fetch(cfg, last, station=None):
        captured["station"] = station
        return (metar, None)

    monkeypatch.setattr(main, "fetch", fake_fetch)

    marker = main._cycle(d, _cfg(), str(p), station_index=0)
    assert marker is None

    import json
    state = json.loads(p.read_text())
    assert state["last_data"] == metar
    assert state["station_index"] == 0
    assert captured["station"] == "KLBB"
    assert "72" in " ".join(d.texts())


def test_cycle_returns_marker_on_failure(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    p.write_text("{}")
    d = FakeDisplay()

    monkeypatch.setattr(main, "fetch", lambda cfg, last, station=None: (None, "offline"))

    marker = main._cycle(d, _cfg(), str(p), station_index=0)
    assert marker == "offline"


def test_is_night_uses_current_tz_offset():
    # 18 UTC + (-5) = 13 local — daytime.
    cfg = SimpleNamespace(TIMEZONE_OFFSET=-5)
    assert main._is_night({"updated_z": "18:00"}, cfg) is False
    # 18 UTC + 0 = 18 local — also daytime.
    cfg = SimpleNamespace(TIMEZONE_OFFSET=0)
    assert main._is_night({"updated_z": "18:00"}, cfg) is False


def test_is_night_after_22_local():
    # 04 UTC + (-5) = 23 local previous day — night.
    cfg = SimpleNamespace(TIMEZONE_OFFSET=-5)
    assert main._is_night({"updated_z": "04:00"}, cfg) is True
    # 02 UTC + (-5) = 21 local — still day boundary at 22.
    assert main._is_night({"updated_z": "02:00"}, cfg) is False
    # 03 UTC + (-5) = 22 local — night threshold.
    assert main._is_night({"updated_z": "03:00"}, cfg) is True


def test_is_night_recomputes_ignoring_stale_hour_field():
    # Cached weather has updated_hour_local=22 (stale, saved with old TZ=0)
    # but current TZ is -5 and current observation is 18Z → local 13 → day.
    cfg = SimpleNamespace(TIMEZONE_OFFSET=-5)
    weather = {"updated_z": "18:00", "updated_hour_local": 22}
    assert main._is_night(weather, cfg) is False


def test_is_night_no_observation():
    cfg = SimpleNamespace(TIMEZONE_OFFSET=-5)
    assert main._is_night(None, cfg) is False
    assert main._is_night({}, cfg) is False
    assert main._is_night({"updated_z": None}, cfg) is False


def test_cycle_switches_station_by_index(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    p.write_text("{}")
    d = FakeDisplay()
    captured = []

    def fake_fetch(cfg, last, station=None):
        captured.append(station)
        return (
            {"station": station, "temp_f": 70, "flight_category": "VFR",
             "wind": "CALM", "summary": "CLR", "updated_z": "10:00",
             "visibility_sm": 10.0, "ceiling_ft": None, "raw": "", "stale": False},
            None,
        )

    monkeypatch.setattr(main, "fetch", fake_fetch)

    main._cycle(d, _cfg(), str(p), station_index=1)

    assert captured == ["KAUS"]


def test_cycle_station_index_wraps(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    p.write_text("{}")
    d = FakeDisplay()
    captured = []

    def fake_fetch(cfg, last, station=None):
        captured.append(station)
        return (
            {"station": station, "temp_f": 70, "flight_category": "VFR",
             "wind": "CALM", "summary": "CLR", "updated_z": "10:00",
             "visibility_sm": 10.0, "ceiling_ft": None, "raw": "", "stale": False},
            None,
        )

    monkeypatch.setattr(main, "fetch", fake_fetch)

    main._cycle(d, _cfg(), str(p), station_index=2)
    assert captured == ["KLBB"]


def test_cycle_offline_uses_last_data(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    last = {"temp_f": 69, "station": "KLBB", "flight_category": "VFR",
            "wind": "180 10kt", "summary": "CLR", "updated_z": "19:30",
            "visibility_sm": 10.0, "ceiling_ft": None, "raw": "",
            "stale": False}
    import json
    p.write_text(json.dumps({"last_data": last, "station_index": 0}))

    d = FakeDisplay()

    def fake_fetch(cfg, prev, station=None):
        stale = dict(prev)
        stale["stale"] = True
        return stale, "offline"

    monkeypatch.setattr(main, "fetch", fake_fetch)

    main._cycle(d, _cfg(), str(p), station_index=0)

    texts = " ".join(d.texts())
    assert "69" in texts
    assert "offline" in texts


def test_stations_helper_falls_back_to_singular():
    cfg = SimpleNamespace(METAR_STATION="KLBB")
    assert main._stations(cfg) == ["KLBB"]


def test_stations_helper_returns_list():
    cfg = SimpleNamespace(METAR_STATIONS=["KAUS", "KDFW", "KLBB"])
    assert main._stations(cfg) == ["KAUS", "KDFW", "KLBB"]


def test_stations_helper_default_when_empty():
    cfg = SimpleNamespace()
    assert main._stations(cfg) == ["KLBB"]


def test_set_speed_is_safe_when_display_lacks_method():
    class NoSpeed:
        pass

    # Should not raise
    main._set_speed(NoSpeed(), 3)


def test_set_speed_forwards_to_display():
    d = FakeDisplay()
    main._set_speed(d, main._UPDATE_TURBO)
    speeds = [args[0] for name, args in d.calls if name == "set_update_speed"]
    assert speeds == [3]


def test_heartbeat_fires_at_interval():
    hb = main.Heartbeat(interval=20.0, duration=0.1, brightness=50)
    d = FakeDisplay()

    # t=0 initial — no blink yet (last=0, now-last = 0 < 20)
    hb.tick(d, 0.0)
    leds = [args[0] for name, args in d.calls if name == "led"]
    assert leds == []

    # t=21 — above interval, blink on
    hb.tick(d, 21.0)
    leds = [args[0] for name, args in d.calls if name == "led"]
    assert leds == [50]
    assert hb.on is True

    # t=21.05 — still within duration, no change
    hb.tick(d, 21.05)
    leds = [args[0] for name, args in d.calls if name == "led"]
    assert leds == [50]

    # t=21.2 — past duration, LED off
    hb.tick(d, 21.2)
    leds = [args[0] for name, args in d.calls if name == "led"]
    assert leds == [50, 0]
    assert hb.on is False


def test_heartbeat_fires_again_after_interval():
    hb = main.Heartbeat(interval=20.0, duration=0.1, brightness=40)
    d = FakeDisplay()

    hb.tick(d, 20.0)    # first blink on
    hb.tick(d, 20.2)    # off
    hb.tick(d, 30.0)    # not yet (interval from last=20, need >= 40)
    assert hb.on is False

    hb.tick(d, 40.0)    # 20s since last, blink again
    assert hb.on is True
    leds = [args[0] for name, args in d.calls if name == "led"]
    assert leds.count(40) == 2


def test_heartbeat_survives_missing_led_method():
    class NoLed:
        pass

    hb = main.Heartbeat(interval=1.0, duration=0.1, brightness=50)
    hb.tick(NoLed(), 2.0)   # would turn on, display.led missing
    hb.tick(NoLed(), 2.2)   # would turn off, display.led missing
    # No exception = pass


def test_refresh_interval_usb(monkeypatch):
    monkeypatch.setattr(main, "_battery_v", lambda: 5.0)
    cfg = SimpleNamespace(REFRESH_MINUTES=15)
    assert main._refresh_interval_s(cfg) == 15 * 60


def test_refresh_interval_lipo_stretches_to_30min(monkeypatch):
    monkeypatch.setattr(main, "_battery_v", lambda: 3.8)
    cfg = SimpleNamespace(REFRESH_MINUTES=15)
    assert main._refresh_interval_s(cfg) == 30 * 60


def test_refresh_interval_lipo_keeps_longer_config(monkeypatch):
    monkeypatch.setattr(main, "_battery_v", lambda: 3.8)
    cfg = SimpleNamespace(REFRESH_MINUTES=60)
    assert main._refresh_interval_s(cfg) == 60 * 60


def test_next_delay_backoff(monkeypatch):
    monkeypatch.setattr(main, "_battery_v", lambda: 5.0)
    cfg = SimpleNamespace(REFRESH_MINUTES=15)
    # 0 failures → normal refresh interval
    assert main._next_delay_s(cfg, 0) == 15 * 60
    # 1 failure → first backoff step (30 s)
    assert main._next_delay_s(cfg, 1) == 30
    # 2 failures → 60 s
    assert main._next_delay_s(cfg, 2) == 60
    # Many failures → caps at the last schedule entry or refresh interval
    assert main._next_delay_s(cfg, 10) == min(main._BACKOFF_SECONDS[-1], 15 * 60)


def test_next_delay_capped_by_short_refresh(monkeypatch):
    monkeypatch.setattr(main, "_battery_v", lambda: 5.0)
    # 1-minute refresh → backoff never exceeds that
    cfg = SimpleNamespace(REFRESH_MINUTES=1)
    for failures in range(1, 6):
        assert main._next_delay_s(cfg, failures) <= 60
