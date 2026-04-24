import time

try:
    import network
except ImportError:
    network = None

try:
    import requests
except ImportError:
    requests = None


import math

_WIFI_TIMEOUT_S = 15.0
_HTTP_TIMEOUT_S = 8.0

# aviationweather.gov airport API returns elevation in metres, airport name,
# and lat/lon; cache per ICAO for the session so we don't re-hit every refresh.
_station_info_cache = {}


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


def _http_get_airport(station):
    url = "https://aviationweather.gov/api/data/airport?ids={0}&format=json".format(station)
    return requests.get(url, timeout=_HTTP_TIMEOUT_S)


def _http_get_taf(station):
    url = "https://aviationweather.gov/api/data/taf?ids={0}&format=json".format(station)
    return requests.get(url, timeout=_HTTP_TIMEOUT_S)


def fetch_taf(station):
    """Returns the raw TAF string for `station` or None on any failure."""
    try:
        r = _http_get_taf(station)
        if r.status_code != 200:
            r.close()
            return None
        try:
            data = r.json()
        except Exception:
            r.close()
            return None
        r.close()
        if not data:
            return None
        return data[0].get("rawTAF")
    except Exception:
        return None


def _short_name(name):
    if not name:
        return None
    first = name.split("/", 1)[0].strip()
    # Title-case without locale surprises
    return " ".join(w.capitalize() for w in first.split())


def _station_info(station):
    if station in _station_info_cache:
        return _station_info_cache[station]
    try:
        r = _http_get_airport(station)
        if r.status_code != 200:
            r.close()
            return None
        try:
            data = r.json()
        except Exception:
            r.close()
            return None
        r.close()
        if not data:
            return None
        entry = data[0]
        elev_m = entry.get("elev")
        info = {
            "elev_ft": int(round(float(elev_m) * 3.28084)) if elev_m is not None else None,
            "name": _short_name(entry.get("name")),
            "lat": entry.get("lat"),
            "lon": entry.get("lon"),
        }
        _station_info_cache[station] = info
        return info
    except Exception:
        return None


def _day_of_year(y, m, d):
    days = [31, 28 + (1 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 0),
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return sum(days[:m-1]) + d


def _sunrise_sunset_utc_hours(y, m, d, lat, lon):
    """NOAA-ish approximation. Returns (sr_utc_h, ss_utc_h) as floats, or (None, None) if polar."""
    try:
        N = _day_of_year(y, m, d)
        gamma = 2 * math.pi / 365 * (N - 1)
        eqtime = 229.18 * (0.000075
                           + 0.001868 * math.cos(gamma)
                           - 0.032077 * math.sin(gamma)
                           - 0.014615 * math.cos(2 * gamma)
                           - 0.040849 * math.sin(2 * gamma))
        decl = (0.006918
                - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
                - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma)
                - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma))
        lat_rad = math.radians(lat)
        cos_ha = (math.cos(math.radians(90.833))
                  / (math.cos(lat_rad) * math.cos(decl))
                  - math.tan(lat_rad) * math.tan(decl))
        if cos_ha > 1 or cos_ha < -1:
            return None, None
        ha = math.degrees(math.acos(cos_ha))
        sr = (12 - ha / 15 - lon / 15 - eqtime / 60) % 24
        ss = (12 + ha / 15 - lon / 15 - eqtime / 60) % 24
        return sr, ss
    except Exception:
        return None, None


def _hhmm_from_hours(h, tz_offset):
    if h is None:
        return None
    local = (h + tz_offset) % 24
    hh = int(local)
    mm = int(round((local - hh) * 60))
    if mm == 60:
        hh = (hh + 1) % 24
        mm = 0
    return "{0:02d}:{1:02d}".format(hh, mm)


def _parse_report_date(report_time):
    if not report_time or "T" not in str(report_time):
        return None
    date_str = str(report_time).split("T", 1)[0]
    try:
        y, m, d = date_str.split("-")
        return int(y), int(m), int(d)
    except Exception:
        return None


def _altim_mb_to_inhg(mb):
    if mb is None:
        return None
    return float(mb) * 0.02953


def _pressure_altitude_ft(elev_ft, altim_inhg):
    if elev_ft is None or altim_inhg is None:
        return None
    return int(round(elev_ft + (29.92 - altim_inhg) * 1000))


def _density_altitude_ft(pa_ft, oat_c):
    if pa_ft is None or oat_c is None:
        return None
    isa_c = 15 - 2 * (pa_ft / 1000.0)
    return int(round(pa_ft + 120 * (oat_c - isa_c)))


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


def _crosswind_components(wind_deg, wind_kt, runway_hdg_deg):
    """Returns (headwind_kt, crosswind_kt, side) or (None, None, None).

    side is "L" if wind is from the left of the runway, "R" from the right,
    or None when there is essentially no crosswind.
    """
    if wind_deg is None or wind_kt is None or runway_hdg_deg is None:
        return None, None, None
    diff_deg = ((wind_deg - runway_hdg_deg) + 180) % 360 - 180
    diff_rad = math.radians(diff_deg)
    hw = int(round(wind_kt * math.cos(diff_rad)))
    xw_signed = wind_kt * math.sin(diff_rad)
    xw = int(round(abs(xw_signed)))
    side = None
    if xw > 0:
        side = "R" if xw_signed > 0 else "L"
    return hw, xw, side


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
    "station_name": None,
    "wind": None,
    "wind_deg": None,
    "wind_kt": None,
    "visibility_sm": None,
    "ceiling_ft": None,
    "raw": None,
    "updated_z": None,
    "updated_hour_local": None,
    "altimeter_inhg": None,
    "dewpoint_f": None,
    "spread_f": None,
    "density_altitude_ft": None,
    "pressure_altitude_ft": None,
    "elevation_ft": None,
    "lat": None,
    "lon": None,
    "sunrise_local": None,
    "sunset_local": None,
    "runway_heading_deg": None,
    "headwind_kt": None,
    "crosswind_kt": None,
    "crosswind_side": None,
    "stale": False,
}


def _parse(payload, station, info, tz_offset, runway_hdg_deg):
    elev_ft = info["elev_ft"] if info else None
    station_name = info["name"] if info else None
    lat = info["lat"] if info else None
    lon = info["lon"] if info else None

    if not payload:
        out = dict(_EMPTY)
        out["station"] = station
        out["station_name"] = station_name
        out["elevation_ft"] = elev_ft
        out["lat"] = lat
        out["lon"] = lon
        out["runway_heading_deg"] = runway_hdg_deg
        out["stale"] = True
        return out
    m = payload[0]
    vis_sm = _parse_vis(m.get("visib"))
    ceiling = _ceiling_ft(m.get("clouds"))
    temp_c = m.get("temp")
    dewp_c = m.get("dewp")
    altim_inhg = _altim_mb_to_inhg(m.get("altim"))
    pa_ft = _pressure_altitude_ft(elev_ft, altim_inhg)
    da_ft = _density_altitude_ft(pa_ft, temp_c)
    temp_f = _c_to_f(temp_c)
    dewp_f = _c_to_f(dewp_c)
    spread_f = None
    if temp_f is not None and dewp_f is not None:
        spread_f = temp_f - dewp_f

    # Sunrise / sunset for the observation date at the station's coordinates
    sunrise_local = None
    sunset_local = None
    report_date = _parse_report_date(m.get("reportTime"))
    if report_date is not None and lat is not None and lon is not None:
        y, mo, d = report_date
        sr_utc, ss_utc = _sunrise_sunset_utc_hours(y, mo, d, lat, lon)
        sunrise_local = _hhmm_from_hours(sr_utc, tz_offset)
        sunset_local = _hhmm_from_hours(ss_utc, tz_offset)

    wdir = m.get("wdir")
    wind_deg = None
    try:
        if wdir is not None and not (isinstance(wdir, str) and str(wdir).upper() == "VRB"):
            wind_deg = int(wdir)
    except Exception:
        wind_deg = None

    wspd = m.get("wspd")
    try:
        wind_kt = int(wspd) if wspd is not None else None
    except Exception:
        wind_kt = None

    hw, xw, xw_side = _crosswind_components(wind_deg, wind_kt, runway_hdg_deg)

    updated_z = _report_hhmm(m.get("reportTime"))
    updated_hour_local = None
    if updated_z:
        try:
            hh_utc = int(updated_z.split(":")[0])
            updated_hour_local = int((hh_utc + tz_offset) % 24)
        except Exception:
            updated_hour_local = None

    return {
        "temp_f": temp_f,
        "summary": _summarize_clouds(m.get("clouds")),
        "flight_category": _flight_category(ceiling, vis_sm),
        "station": m.get("icaoId") or station,
        "station_name": station_name,
        "wind": _format_wind(wdir, wspd, m.get("wgst")),
        "wind_deg": wind_deg,
        "wind_kt": wind_kt,
        "visibility_sm": vis_sm,
        "ceiling_ft": ceiling,
        "raw": m.get("rawOb"),
        "updated_z": updated_z,
        "updated_hour_local": updated_hour_local,
        "altimeter_inhg": round(altim_inhg, 2) if altim_inhg is not None else None,
        "dewpoint_f": dewp_f,
        "spread_f": spread_f,
        "density_altitude_ft": da_ft,
        "pressure_altitude_ft": pa_ft,
        "elevation_ft": elev_ft,
        "lat": lat,
        "lon": lon,
        "sunrise_local": sunrise_local,
        "sunset_local": sunset_local,
        "runway_heading_deg": runway_hdg_deg,
        "headwind_kt": hw,
        "crosswind_kt": xw,
        "crosswind_side": xw_side,
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
        info = _station_info(station)
        tz_offset = getattr(cfg, "TIMEZONE_OFFSET", 0)
        runways = getattr(cfg, "RUNWAYS", None) or {}
        runway_hdg_deg = runways.get(station)
        return _parse(payload, station, info, tz_offset, runway_hdg_deg), None
    except Exception:
        if last_data is not None:
            return _stale_copy(last_data), "offline"
        out = dict(_EMPTY)
        out["station"] = station
        out["stale"] = True
        return out, "offline"
