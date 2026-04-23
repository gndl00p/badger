from tests.fakes.display import FakeDisplay

from render import render


_WEATHER = {
    "temp_f": 86,
    "summary": "FEW050",
    "flight_category": "VFR",
    "station": "KLBB",
    "wind": "200 5kt G15",
    "visibility_sm": 10.0,
    "ceiling_ft": None,
    "raw": "KLBB 232200Z 20005G15KT 10SM FEW050 30/M04 A2998",
    "updated_z": "22:00",
    "stale": False,
}


def test_renders_big_temp_and_category():
    d = FakeDisplay()
    render(d, _WEATHER)
    big = [args[0] for name, args in d.calls if name == "text" and args[4] >= 4]
    assert any("86" in t for t in big)
    assert any("VFR" in t for t in big)


def test_renders_station_wind_clouds():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join(d.texts())
    assert "KLBB" in texts
    assert "200" in texts and "5kt" in texts
    assert "FEW050" in texts


def test_renders_visibility():
    d = FakeDisplay()
    render(d, _WEATHER)
    assert "10SM" in " ".join(d.texts())


def test_renders_updated_zulu_on_station_line():
    d = FakeDisplay()
    render(d, _WEATHER)
    # Timestamp lives on the station line now (the big cat obscures the top-right corner).
    station_lines = [args[0] for name, args in d.calls if name == "text" and "KLBB" in args[0]]
    assert station_lines
    assert "22:00Z" in station_lines[0]


def test_stale_marker_rendered():
    d = FakeDisplay()
    render(d, _WEATHER, stale_marker="offline")
    assert "offline" in " ".join(d.texts())


def test_none_weather_shows_placeholders():
    d = FakeDisplay()
    render(d, None, stale_marker="offline")
    texts = " ".join(d.texts())
    assert "offline" in texts
    assert "--" in texts


def test_horizontal_divider_drawn():
    d = FakeDisplay()
    render(d, _WEATHER)
    lines = [args for name, args in d.calls if name == "line"]
    assert any(a[1] == a[3] for a in lines)


def test_low_temp():
    w = dict(_WEATHER, temp_f=5, flight_category="LIFR")
    d = FakeDisplay()
    render(d, w)
    texts = " ".join(d.texts())
    assert "5F" in texts
    assert "LIFR" in texts
