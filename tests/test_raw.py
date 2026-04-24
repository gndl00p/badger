from tests.fakes.display import FakeDisplay

import raw


_WEATHER = {
    "station": "KLBB",
    "temp_f": 86,
    "dewpoint_f": 46,
    "spread_f": 40,
    "altimeter_inhg": 29.64,
    "density_altitude_ft": 5600,
    "pressure_altitude_ft": 3500,
    "raw": "KLBB 232200Z 23005KT 10SM FEW050 31/M06 A2998",
}


def test_renders_raw_metar_line():
    d = FakeDisplay()
    raw.render(d, _WEATHER)
    texts = " ".join(d.texts())
    assert "KLBB" in texts
    assert "23005KT" in texts


def test_renders_altimeter():
    d = FakeDisplay()
    raw.render(d, _WEATHER)
    texts = " ".join(d.texts())
    assert "ALT 29.64" in texts


def test_renders_dewpoint_and_spread():
    d = FakeDisplay()
    raw.render(d, _WEATHER)
    texts = " ".join(d.texts())
    assert "DEW 46F" in texts
    assert "SPD 40F" in texts


def test_renders_da_and_pa():
    d = FakeDisplay()
    raw.render(d, _WEATHER)
    texts = " ".join(d.texts())
    assert "DA 5600" in texts
    assert "PA 3500" in texts


def test_header_and_back_hint():
    d = FakeDisplay()
    raw.render(d, _WEATHER)
    texts = " ".join(d.texts())
    assert "Details" in texts
    assert "B back" in texts


def test_missing_raw_placeholder():
    d = FakeDisplay()
    raw.render(d, {"station": "KLBB"})
    texts = " ".join(d.texts())
    assert "no raw METAR" in texts


def test_none_weather_placeholder():
    d = FakeDisplay()
    raw.render(d, None)
    texts = " ".join(d.texts())
    assert "no raw METAR" in texts


def test_divider_drawn():
    d = FakeDisplay()
    raw.render(d, _WEATHER)
    lines = [args for name, args in d.calls if name == "line"]
    assert any(a[1] == 24 for a in lines)
