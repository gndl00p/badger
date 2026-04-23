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
        "rawOb": "KLBB 232200Z 20005G15KT 10SM FEW050 30/M04 A2998",
        "clouds": [{"cover": "FEW", "base": 5000}],
    }]


def test_fetch_happy_path(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.side_effect = [False, True]
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    response = MagicMock(status_code=200)
    response.json.return_value = _metar_payload()
    monkeypatch.setattr(fetcher, "_http_get_metar", lambda station: response)

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
