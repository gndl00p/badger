import time

try:
    import network
except ImportError:
    network = None

try:
    import requests
except ImportError:
    requests = None


_WIFI_TIMEOUT_S = 15.0
_HTTP_TIMEOUT_S = 8.0


def _make_wlan():
    return network.WLAN(network.STA_IF)


def _connect_wifi(cfg):
    w = _make_wlan()
    w.active(True)
    if not w.isconnected():
        w.connect(cfg.WIFI_SSID, cfg.WIFI_PSK)
    deadline = time.time() + _WIFI_TIMEOUT_S
    while not w.isconnected():
        if time.time() > deadline:
            return False
        time.sleep(0.25)
    return True


def _http_get_metar(station):
    url = "https://aviationweather.gov/api/data/metar?ids={0}&format=json".format(station)
    return requests.get(url, timeout=_HTTP_TIMEOUT_S)


def _c_to_f(c):
    if c is None:
        return None
    return int(round(c * 9 / 5 + 32))


def _parse_vis(v):
    if v is None:
        return None
    s = str(v).replace("+", "").strip()
    if not s:
        return None
    if "/" in s:
        total = 0.0
        for token in s.split():
            if "/" in token:
                num, den = token.split("/")
                total += float(num) / float(den)
            else:
                total += float(token)
        return total
    try:
        return float(s)
    except ValueError:
        return None


def _ceiling_ft(clouds):
    if not clouds:
        return None
    for layer in clouds:
        cover = str(layer.get("cover", "")).upper()
        base = layer.get("base")
        if cover in ("BKN", "OVC", "VV") and base is not None:
            return int(base)
    return None


def _flight_category(ceiling_ft, vis_sm):
    c = ceiling_ft
    v = vis_sm
    if (c is not None and c < 500) or (v is not None and v < 1):
        return "LIFR"
    if (c is not None and c < 1000) or (v is not None and v < 3):
        return "IFR"
    if (c is not None and c <= 3000) or (v is not None and v <= 5):
        return "MVFR"
    return "VFR"


def _format_wind(wdir, wspd, wgst):
    if wspd is None or wspd == 0:
        return "CALM"
    if wdir is None or (isinstance(wdir, str) and str(wdir).upper() == "VRB") or wdir == 0:
        base = "VRB {0}kt".format(int(wspd))
    else:
        base = "{0:03d} {1}kt".format(int(wdir), int(wspd))
    if wgst:
        base += " G{0}".format(int(wgst))
    return base


def _summarize_clouds(clouds):
    if not clouds:
        return "CLR"
    parts = []
    for layer in clouds:
        cover = str(layer.get("cover", "")).upper()
        if cover in ("CLR", "SKC", "NCD"):
            return "CLR"
        base = layer.get("base")
        if base is not None:
            parts.append("{0}{1:03d}".format(cover, int(base / 100)))
        else:
            parts.append(cover)
        if len(parts) == 3:
            break
    return " ".join(parts)


def _report_hhmm(report_time):
    if not report_time:
        return None
    s = str(report_time)
    if "T" in s:
        s = s.split("T", 1)[1]
    elif " " in s:
        s = s.split(" ", 1)[1]
    return s[:5]


def _stale_copy(data):
    out = dict(data)
    out["stale"] = True
    return out


_EMPTY = {
    "temp_f": None,
    "summary": "no data",
    "flight_category": None,
    "station": None,
    "wind": None,
    "visibility_sm": None,
    "ceiling_ft": None,
    "raw": None,
    "updated_z": None,
    "stale": False,
}


def _parse(payload, station):
    if not payload:
        out = dict(_EMPTY)
        out["station"] = station
        out["stale"] = True
        return out
    m = payload[0]
    vis_sm = _parse_vis(m.get("visib"))
    ceiling = _ceiling_ft(m.get("clouds"))
    return {
        "temp_f": _c_to_f(m.get("temp")),
        "summary": _summarize_clouds(m.get("clouds")),
        "flight_category": _flight_category(ceiling, vis_sm),
        "station": m.get("icaoId") or station,
        "wind": _format_wind(m.get("wdir"), m.get("wspd"), m.get("wgst")),
        "visibility_sm": vis_sm,
        "ceiling_ft": ceiling,
        "raw": m.get("rawOb"),
        "updated_z": _report_hhmm(m.get("reportTime")),
        "stale": False,
    }


def fetch(cfg, last_data, station=None):
    if station is None:
        stations = getattr(cfg, "METAR_STATIONS", None)
        if stations:
            station = stations[0]
        else:
            station = getattr(cfg, "METAR_STATION", "KLBB")

    if not _connect_wifi(cfg):
        if last_data is not None:
            return _stale_copy(last_data), "offline"
        out = dict(_EMPTY)
        out["station"] = station
        out["stale"] = True
        return out, "offline"

    try:
        r = _http_get_metar(station)
        if r.status_code != 200:
            r.close()
            if last_data is not None:
                return _stale_copy(last_data), "offline"
            out = dict(_EMPTY)
            out["station"] = station
            out["stale"] = True
            return out, "offline"
        try:
            payload = r.json()
            r.close()
        except (ValueError, Exception):
            r.close()
            if last_data is not None:
                return _stale_copy(last_data), "bad payload"
            out = dict(_EMPTY)
            out["station"] = station
            out["stale"] = True
            return out, "bad payload"
        return _parse(payload, station), None
    except Exception:
        if last_data is not None:
            return _stale_copy(last_data), "offline"
        out = dict(_EMPTY)
        out["station"] = station
        out["stale"] = True
        return out, "offline"
