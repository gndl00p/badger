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

    main._cycle(d, _cfg(), str(p), station_index=0)

    import json
    state = json.loads(p.read_text())
    assert state["last_data"] == metar
    assert state["station_index"] == 0
    assert captured["station"] == "KLBB"
    assert "72" in " ".join(d.texts())


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

    # index 2 with 2 stations wraps to KLBB
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
