from tests.fakes.display import FakeDisplay

from render import render


_WEATHER = {
    "temp_f": 91,
    "dewpoint_f": 46,
    "summary": "FEW050",
    "flight_category": "VFR",
    "station": "KLBB",
    "station_name": "Lubbock",
    "wind": "200 5kt G15",
    "wind_deg": 200,
    "wind_kt": 5,
    "visibility_sm": 10.0,
    "ceiling_ft": None,
    "raw": "KLBB 232200Z 20005G15KT 10SM FEW050",
    "updated_z": "22:00",
    "updated_hour_local": 17,
    "altimeter_inhg": 29.92,
    "spread_f": 45,
    "density_altitude_ft": 5800,
    "pressure_altitude_ft": 3500,
    "elevation_ft": 3282,
    "lat": 33.66,
    "lon": -101.82,
    "sunrise_local": "06:45",
    "sunset_local": "20:15",
    "stale": False,
}


def test_renders_header_with_station_and_name():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = [args[0] for name, args in d.calls if name == "text"]
    assert any("KLBB" in t and "Lubbock" in t for t in texts)


def test_header_carries_updated_zulu_time():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join(args[0] for name, args in d.calls if name == "text")
    assert "22:00Z" in texts


def test_renders_big_temp_and_category():
    d = FakeDisplay()
    render(d, _WEATHER)
    big = [args[0] for name, args in d.calls if name == "text" and args[4] >= 4]
    assert any("91" in t for t in big)
    assert any("VFR" in t for t in big)


def test_body_row_wind_and_tempdew_at_scale_2():
    d = FakeDisplay()
    render(d, _WEATHER)
    body = [args for name, args in d.calls if name == "text" and args[4] == 2]
    wind_lines = [t for t, *_ in body if "WIND" in t]
    assert wind_lines
    assert "200" in wind_lines[0]
    assert "91/46" in wind_lines[0]


def test_body_row_clouds_and_vis_at_scale_2():
    d = FakeDisplay()
    render(d, _WEATHER)
    body = [args for name, args in d.calls if name == "text" and args[4] == 2]
    cld_lines = [t for t, *_ in body if t.startswith("CLD")]
    assert cld_lines
    assert "FEW050" in cld_lines[0]
    assert "10SM" in cld_lines[0]


def test_body_row_da_at_scale_2():
    d = FakeDisplay()
    render(d, _WEATHER)
    body = [args for name, args in d.calls if name == "text" and args[4] == 2]
    da_lines = [t for t, *_ in body if t.startswith("DA")]
    assert da_lines
    assert "5800" in da_lines[0]


def test_body_row_da_includes_ceiling_when_no_runway():
    d = FakeDisplay()
    w = dict(_WEATHER, ceiling_ft=8000)
    render(d, w)
    body = [args[0] for name, args in d.calls if name == "text" and args[4] == 2]
    da_lines = [t for t in body if t.startswith("DA")]
    assert da_lines
    assert "CEIL 8000" in da_lines[0]


def test_no_temp_dew_when_dewpoint_missing():
    d = FakeDisplay()
    w = dict(_WEATHER, dewpoint_f=None)
    render(d, w)
    body = [args[0] for name, args in d.calls if name == "text" and args[4] == 2]
    wind_lines = [t for t in body if "WIND" in t]
    assert wind_lines
    assert "/" not in wind_lines[0]


def test_runway_appended_to_da_row_when_configured():
    d = FakeDisplay()
    w = dict(_WEATHER, runway_heading_deg=170, headwind_kt=12,
             crosswind_kt=5, crosswind_side="L")
    render(d, w)
    body = [args[0] for name, args in d.calls if name == "text" and args[4] == 2]
    da_lines = [t for t in body if t.startswith("DA")]
    assert da_lines
    assert "RWY17" in da_lines[0]
    assert "HW12" in da_lines[0]
    assert "XW5L" in da_lines[0]


def test_no_runway_in_da_row_when_not_configured():
    d = FakeDisplay()
    render(d, _WEATHER)
    body = [args[0] for name, args in d.calls if name == "text" and args[4] == 2]
    da_lines = [t for t in body if t.startswith("DA")]
    assert da_lines
    assert "RWY" not in da_lines[0]


def test_no_sunrise_sunset_on_main():
    d = FakeDisplay()
    render(d, _WEATHER)
    texts = " ".join(args[0] for name, args in d.calls if name == "text")
    assert "SR " not in texts
    assert "SS " not in texts


def test_inverted_category_for_ifr():
    d = FakeDisplay()
    w = dict(_WEATHER, flight_category="IFR")
    render(d, w)
    rects = [args for name, args in d.calls if name == "rectangle"]
    big_rects = [r for r in rects if 10 <= r[1] <= 20 and r[3] >= 40]
    assert big_rects


def test_plain_category_for_vfr():
    d = FakeDisplay()
    render(d, _WEATHER)
    rects = [args for name, args in d.calls if name == "rectangle"]
    # Only the full-screen clear rect.
    assert len(rects) == 1


def test_two_dividers_drawn():
    d = FakeDisplay()
    render(d, _WEATHER)
    lines = [args for name, args in d.calls if name == "line"]
    ys = sorted({(a[1], a[3]) for a in lines})
    assert (12, 12) in ys
    assert (62, 62) in ys


def test_night_inverts_colors():
    d = FakeDisplay()
    render(d, _WEATHER, invert=True)
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    assert pens[0] == 0


def test_day_normal_colors():
    d = FakeDisplay()
    render(d, _WEATHER, invert=False)
    pens = [args[0] for name, args in d.calls if name == "set_pen"]
    assert pens[0] == 15


def test_low_temp_lifr():
    w = dict(_WEATHER, temp_f=5, flight_category="LIFR")
    d = FakeDisplay()
    render(d, w)
    big = [args[0] for name, args in d.calls if name == "text" and args[4] >= 4]
    assert any("5F" in t for t in big)
    assert any("LIFR" in t for t in big)


def test_stale_marker_replaces_runway_slot():
    d = FakeDisplay()
    render(d, _WEATHER, stale_marker="offline")
    texts = " ".join(args[0] for name, args in d.calls if name == "text")
    assert "offline" in texts


def test_none_weather_safe():
    d = FakeDisplay()
    render(d, None, stale_marker="offline")
    texts = " ".join(args[0] for name, args in d.calls if name == "text")
    assert "offline" in texts
    assert "--F" in texts or "--" in texts
