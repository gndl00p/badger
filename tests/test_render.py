from tests.fakes.display import FakeDisplay

from render import render


_WEATHER = {
    "temp_f": 86,
    "dewpoint_f": 46,
    "summary": "FEW050",
    "flight_category": "VFR",
    "station": "KLBB",
    "station_name": "Lubbock",
    "wind": "200 5kt G15",
    "wind_deg": 200,
    "visibility_sm": 10.0,
    "ceiling_ft": None,
    "raw": "KLBB 232200Z 20005G15KT 10SM FEW050 30/M04 A2998",
    "updated_z": "22:00",
    "density_altitude_ft": 5800,
    "sunrise_local": "06:45",
    "sunset_local": "20:15",
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


def test_renders_density_altitude_on_station_line():
    d = FakeDisplay()
    render(d, _WEATHER)
    station_lines = [args[0] for name, args in d.calls if name == "text" and "KLBB" in args[0]]
    assert station_lines
    assert "DA5800" in station_lines[0]


def test_no_da_when_unknown():
    d = FakeDisplay()
    w = dict(_WEATHER)
    w["density_altitude_ft"] = None
    render(d, w)
    texts = " ".join(d.texts())
    assert "DA" not in texts


def test_renders_temp_dewpoint_on_wind_line():
    d = FakeDisplay()
    render(d, _WEATHER)
    wind_lines = [args[0] for name, args in d.calls if name == "text" and "200" in args[0]]
    assert wind_lines
    assert "86/46" in wind_lines[0]


def test_no_temp_dew_when_dewpoint_unknown():
    d = FakeDisplay()
    w = dict(_WEATHER)
    w["dewpoint_f"] = None
    render(d, w)
    wind_lines = [args[0] for name, args in d.calls if name == "text" and "200" in args[0]]
    assert wind_lines
    assert "/" not in wind_lines[0]


def test_renders_station_name():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join(d.texts())
    assert "Lubbock" in texts


def test_renders_sunrise_sunset():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join(d.texts())
    assert "SR 06:45" in texts
    assert "SS 20:15" in texts


def test_inverted_category_for_ifr():
    d = FakeDisplay()
    w = dict(_WEATHER, flight_category="IFR")
    render(d, w)
    # Big inverted block = a rectangle call in the top-right region + a WHITE pen switch.
    rects = [args for name, args in d.calls if name == "rectangle"]
    big_rects = [r for r in rects if r[1] <= 10 and r[3] >= 40]  # y1 top, tall
    assert big_rects
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    assert 15 in pens  # switched to WHITE for the inverted text


def test_plain_category_for_vfr():
    d = FakeDisplay()
    render(d, _WEATHER)
    # Only the clear-white full-screen rectangle should be at y=0.
    top_rects = [args for name, args in d.calls if name == "rectangle" and args[0] == 0 and args[1] == 0]
    other_big_rects = [args for name, args in d.calls if name == "rectangle" and args[1] < 60 and (args[0], args[1]) != (0, 0)]
    assert not other_big_rects


def test_wind_arrow_drawn_when_wind_deg_present():
    d = FakeDisplay()
    render(d, _WEATHER)
    lines = [args for name, args in d.calls if name == "line"]
    # At least: the horizontal divider (y1==y2==64) plus the arrow shaft + two arrowhead lines
    assert len(lines) >= 4


def test_no_arrow_when_wind_deg_missing():
    d = FakeDisplay()
    w = dict(_WEATHER, wind_deg=None)
    render(d, w)
    lines = [args for name, args in d.calls if name == "line"]
    # Only the divider remains
    assert len(lines) == 1


def test_renders_crosswind_headwind_on_clouds_line():
    d = FakeDisplay()
    w = dict(_WEATHER, headwind_kt=12, crosswind_kt=5, crosswind_side="L")
    render(d, w)
    clouds_lines = [args[0] for name, args in d.calls if name == "text" and "FEW" in args[0]]
    assert clouds_lines
    assert "HW12 XW5L" in clouds_lines[0]


def test_no_crosswind_when_runway_not_configured():
    d = FakeDisplay()
    render(d, _WEATHER)
    clouds_lines = [args[0] for name, args in d.calls if name == "text" and "FEW" in args[0]]
    assert clouds_lines
    assert "HW" not in clouds_lines[0]


def test_night_inverts_colors():
    d = FakeDisplay()
    w = dict(_WEATHER, updated_hour_local=23)
    render(d, w)
    # First pen call after clear is BLACK background → 0 is set first (rectangle fill bg)
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    # Background = BLACK (0) in night mode, then foreground WHITE (15)
    assert pens[0] == 0
    assert 15 in pens


def test_day_normal_colors():
    d = FakeDisplay()
    w = dict(_WEATHER, updated_hour_local=14)
    render(d, w)
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    # Background = WHITE (15) in day mode, then foreground BLACK (0)
    assert pens[0] == 15
    assert 0 in pens


def test_explicit_invert_wins():
    d = FakeDisplay()
    w = dict(_WEATHER, updated_hour_local=14)
    render(d, w, invert=True)
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    assert pens[0] == 0


def test_renders_last_updated_stamp():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = [args[0] for name, args in d.calls if name == "text"]
    assert any("last updated 22:00Z" in t for t in texts)


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
