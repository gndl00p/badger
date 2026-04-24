from types import SimpleNamespace
from unittest.mock import MagicMock

import fetcher


def _cfg():
    return SimpleNamespace(
        WIFI_SSID="net",
        WIFI_PSK="pw",
        METAR_STATIONS=["KLBB"],
    )


def test_fetch_uses_explicit_station_arg(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    captured = {}

    def spy(station):
        captured["station"] = station
        r = MagicMock(status_code=200)
        r.json.return_value = [{"icaoId": station, "temp": 10, "wdir": 0,
                                "wspd": 0, "visib": "10", "rawOb": "",
                                "clouds": [], "reportTime": "2026-04-23T10:00:00Z"}]
        return r

    monkeypatch.setattr(fetcher, "_http_get_metar", spy)

    _, _ = fetcher.fetch(_cfg(), last_data=None, station="KAUS")
    assert captured["station"] == "KAUS"


def test_fetch_default_station_from_stations_list(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    captured = {}

    def spy(station):
        captured["station"] = station
        r = MagicMock(status_code=200)
        r.json.return_value = [{"icaoId": station, "temp": 10, "wdir": 0,
                                "wspd": 0, "visib": "10", "rawOb": "",
                                "clouds": [], "reportTime": "2026-04-23T10:00:00Z"}]
        return r

    monkeypatch.setattr(fetcher, "_http_get_metar", spy)

    cfg = SimpleNamespace(
        WIFI_SSID="n", WIFI_PSK="p",
        METAR_STATIONS=["KDFW", "KLBB"],
    )
    fetcher.fetch(cfg, last_data=None)
    assert captured["station"] == "KDFW"


def _metar_payload():
    return [{
        "icaoId": "KLBB",
        "reportTime": "2026-04-23T22:00:00.000Z",
        "temp": 30,
        "dewp": -3.9,
        "wdir": 200,
        "wspd": 5,
        "wgst": 15,
        "visib": "10+",
        "altim": 1015.0,
        "rawOb": "KLBB 232200Z 20005G15KT 10SM FEW050 30/M04 A2998",
        "clouds": [{"cover": "FEW", "base": 5000}],
    }]


def test_computes_da_pa_dewpoint_spread(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=200)
    response.json.return_value = _metar_payload()
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)
    monkeypatch.setattr(fetcher, "_station_info", lambda station: {
        "elev_ft": 3282, "name": "Lubbock", "lat": 33.66, "lon": -101.82,
    })

    data, _ = fetcher.fetch(_cfg(), last_data=None)

    # Pressure altitude: 3282 + (29.92 - 1015*0.02953)*1000
    #                  = 3282 + (29.92 - 29.972) * 1000
    #                  = 3282 + -52 ≈ 3230 (rounded)
    assert data["pressure_altitude_ft"] is not None
    assert 3200 <= data["pressure_altitude_ft"] <= 3260

    # ISA at ~3230 = 15 - 6.46 = 8.54 C ; DA = PA + 120*(30-8.54) ≈ 3230 + 2575 ≈ 5805
    assert data["density_altitude_ft"] is not None
    assert 5700 <= data["density_altitude_ft"] <= 5900

    assert data["altimeter_inhg"] is not None
    assert 29.95 <= data["altimeter_inhg"] <= 30.00

    # Dewpoint: -3.9 C → 25 F
    assert data["dewpoint_f"] == 25

    # Spread: 86 - 25 = 61
    assert data["spread_f"] == 61

    assert data["elevation_ft"] == 3282


def test_station_info_cache_hit_avoids_second_call(monkeypatch):
    calls = []

    class R:
        status_code = 200
        def json(self):
            return [{"icaoId": "KLBB", "elev": 1000, "name": "LUBBOCK/PRESTON SMITH",
                     "lat": 33.66, "lon": -101.82}]
        def close(self):
            pass

    def spy(station):
        calls.append(station)
        return R()

    monkeypatch.setattr(fetcher, "_http_get_airport", spy)
    fetcher._station_info_cache.clear()

    first = fetcher._station_info("KLBB")
    second = fetcher._station_info("KLBB")
    assert first == second
    assert first["elev_ft"] == 3281  # 1000 m * 3.28084
    assert first["name"] == "Lubbock"
    assert first["lat"] == 33.66
    assert calls == ["KLBB"]


def test_sunrise_sunset_approx_for_klbb():
    # ~May in Lubbock: sunrise ~06:50 CDT, sunset ~20:30 CDT
    sr, ss = fetcher._sunrise_sunset_utc_hours(2026, 5, 1, 33.66, -101.82)
    assert sr is not None and ss is not None
    # UTC then apply -5 offset (CDT)
    sr_hhmm = fetcher._hhmm_from_hours(sr, -5)
    ss_hhmm = fetcher._hhmm_from_hours(ss, -5)
    assert sr_hhmm.startswith("06:") or sr_hhmm.startswith("07:")
    assert ss_hhmm.startswith("20:") or ss_hhmm.startswith("21:")


def test_wind_deg_numeric_when_not_vrb(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=200)
    response.json.return_value = _metar_payload()
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)
    monkeypatch.setattr(fetcher, "_station_info", lambda station: None)

    data, _ = fetcher.fetch(_cfg(), last_data=None)
    assert data["wind_deg"] == 200


def test_crosswind_components_left_wind():
    # Runway 170, wind from 140 @ 10 kt → 30° left of runway
    hw, xw, side = fetcher._crosswind_components(140, 10, 170)
    assert hw == 9        # ~10 * cos(30°)
    assert xw == 5        # ~10 * |sin(30°)|
    assert side == "L"


def test_crosswind_components_right_wind():
    # Runway 170, wind from 200 @ 10 kt → 30° right of runway
    hw, xw, side = fetcher._crosswind_components(200, 10, 170)
    assert hw == 9
    assert xw == 5
    assert side == "R"


def test_crosswind_components_pure_tailwind():
    hw, xw, side = fetcher._crosswind_components(350, 10, 170)
    assert hw == -10
    assert xw == 0
    assert side is None


def test_crosswind_components_missing_inputs():
    assert fetcher._crosswind_components(None, 10, 170) == (None, None, None)
    assert fetcher._crosswind_components(200, None, 170) == (None, None, None)
    assert fetcher._crosswind_components(200, 10, None) == (None, None, None)


def test_crosswind_populated_when_runway_configured(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=200)
    response.json.return_value = _metar_payload()
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)
    monkeypatch.setattr(fetcher, "_station_info", lambda station: None)

    cfg = SimpleNamespace(
        WIFI_SSID="n", WIFI_PSK="p",
        METAR_STATIONS=["KLBB"],
        RUNWAYS={"KLBB": 170},
    )
    data, _ = fetcher.fetch(cfg, last_data=None)
    assert data["runway_heading_deg"] == 170
    # Wind 200 on rwy 170 → right crosswind
    assert data["crosswind_side"] == "R"
    assert data["crosswind_kt"] is not None


def test_updated_hour_local_applies_tz_offset(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=200)
    # reportTime at 22:00 UTC
    response.json.return_value = [{
        "icaoId": "KLBB", "reportTime": "2026-04-24T22:00:00.000Z",
        "temp": 20, "wdir": 180, "wspd": 5,
        "visib": "10", "rawOb": "", "clouds": [],
    }]
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)
    monkeypatch.setattr(fetcher, "_station_info", lambda station: None)

    cfg = SimpleNamespace(
        WIFI_SSID="n", WIFI_PSK="p",
        METAR_STATIONS=["KLBB"],
        TIMEZONE_OFFSET=-5,
    )
    data, _ = fetcher.fetch(cfg, last_data=None)
    # 22 UTC + (-5) = 17 local
    assert data["updated_hour_local"] == 17


def test_fetch_taf_happy_path(monkeypatch):
    r = MagicMock(status_code=200)
    r.json.return_value = [{"rawTAF": "TAF KLBB 242330Z 2500/2524 21012KT P6SM SCT060"}]
    monkeypatch.setattr(fetcher, "_http_get_taf", lambda station: r)
    assert fetcher.fetch_taf("KLBB").startswith("TAF KLBB")


def test_fetch_taf_error_returns_none(monkeypatch):
    def boom(station):
        raise OSError("boom")
    monkeypatch.setattr(fetcher, "_http_get_taf", boom)
    assert fetcher.fetch_taf("KLBB") is None


def test_fetch_taf_empty_returns_none(monkeypatch):
    r = MagicMock(status_code=200)
    r.json.return_value = []
    monkeypatch.setattr(fetcher, "_http_get_taf", lambda station: r)
    assert fetcher.fetch_taf("KLBB") is None


def test_da_omitted_when_elevation_unknown(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=200)
    response.json.return_value = _metar_payload()
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)
    monkeypatch.setattr(fetcher, "_station_info", lambda station: None)

    data, _ = fetcher.fetch(_cfg(), last_data=None)
    assert data["density_altitude_ft"] is None
    assert data["pressure_altitude_ft"] is None
    # Dewpoint + altim still work without elevation
    assert data["altimeter_inhg"] is not None
    assert data["dewpoint_f"] is not None


def test_fetch_happy_path(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.side_effect = [False, True]
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    response = MagicMock(status_code=200)
    response.json.return_value = _metar_payload()
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)
    monkeypatch.setattr(fetcher, "_station_info", lambda station: {
        "elev_ft": 3282, "name": "Lubbock", "lat": 33.66, "lon": -101.82,
    })

    data, marker = fetcher.fetch(_cfg(), last_data=None)

    wlan.connect.assert_called_with("net", "pw")
    assert marker is None
    assert data["temp_f"] == 86  # 30 C → 86 F
    assert data["flight_category"] == "VFR"
    assert data["station"] == "KLBB"
    assert data["wind"] == "200 5kt G15"
    assert data["summary"] == "FEW050"
    assert data["visibility_sm"] == 10.0
    assert data["updated_z"] == "22:00"
    assert data["raw"].startswith("KLBB 232200Z")
    assert data["stale"] is False


def test_wifi_timeout_returns_last_with_offline(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = False
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    monkeypatch.setattr(fetcher, "_WIFI_TIMEOUT_S", 0.01)

    last = {"temp_f": 69, "station": "KLBB"}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert marker == "offline"
    assert data["temp_f"] == 69
    assert data["stale"] is True


def test_wifi_timeout_no_history_returns_stale_default(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = False
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    monkeypatch.setattr(fetcher, "_WIFI_TIMEOUT_S", 0.01)

    data, marker = fetcher.fetch(_cfg(), last_data=None)

    assert marker == "offline"
    assert data["temp_f"] is None
    assert data["station"] == "KLBB"
    assert data["stale"] is True


def test_http_error_returns_last_with_offline(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    def boom(station):
        raise OSError("conn reset")

    monkeypatch.setattr(fetcher, "_http_get_metar", boom)

    last = {"temp_f": 69, "station": "KLBB"}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert marker == "offline"
    assert data["stale"] is True


def test_non_200_returns_last_with_offline(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=500)
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)

    last = {"temp_f": 69, "station": "KLBB"}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert marker == "offline"
    assert data["temp_f"] == 69


def test_bad_payload_returns_last_with_marker(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=200)
    response.json.side_effect = ValueError("bad json")
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)

    last = {"temp_f": 69, "station": "KLBB"}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert marker == "bad payload"
    assert data["stale"] is True


def test_flight_category_ifr(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    response = MagicMock(status_code=200)
    response.json.return_value = [{
        "icaoId": "KLBB",
        "temp": 10, "wdir": 360, "wspd": 5,
        "visib": "2", "rawOb": "",
        "clouds": [{"cover": "BKN", "base": 700}],
    }]
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)

    data, marker = fetcher.fetch(_cfg(), last_data=None)

    assert marker is None
    assert data["flight_category"] == "IFR"
    assert data["ceiling_ft"] == 700


def test_flight_category_lifr_with_fraction_vis(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    response = MagicMock(status_code=200)
    response.json.return_value = [{
        "icaoId": "KLBB",
        "temp": 5, "wdir": 0, "wspd": 0,
        "visib": "1/2", "rawOb": "",
        "clouds": [{"cover": "OVC", "base": 300}],
    }]
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)

    data, _ = fetcher.fetch(_cfg(), last_data=None)

    assert data["flight_category"] == "LIFR"
    assert data["wind"] == "CALM"
    assert data["visibility_sm"] == 0.5


def test_cloud_summary_metar_short_form(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    response = MagicMock(status_code=200)
    response.json.return_value = [{
        "icaoId": "KLBB",
        "temp": 20, "wdir": 180, "wspd": 10,
        "visib": "10", "rawOb": "",
        "clouds": [
            {"cover": "FEW", "base": 6000},
            {"cover": "BKN", "base": 8000},
        ],
    }]
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)

    data, _ = fetcher.fetch(_cfg(), last_data=None)
    assert data["summary"] == "FEW060 BKN080"
