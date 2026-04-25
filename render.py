import math

WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128

_CAT_SCALE = 5
_CAT_CHAR_W = 30  # bitmap8 char at scale 5


def _is_night_hour(hour):
    if hour is None:
        return False
    return hour >= 22 or hour < 6


def _draw_wind_arrow(display, cx, cy, r, wind_deg):
    if wind_deg is None:
        return
    angle = math.radians((wind_deg + 180) % 360)
    dx = math.sin(angle)
    dy = -math.cos(angle)
    tip = (int(cx + dx * r), int(cy + dy * r))
    tail = (int(cx - dx * r), int(cy - dy * r))
    display.line(tail[0], tail[1], tip[0], tip[1])
    head_r = 5
    spread = math.radians(30)
    for sign in (1, -1):
        back = angle + math.pi + sign * spread
        hx = int(tip[0] + math.sin(back) * head_r)
        hy = int(tip[1] - math.cos(back) * head_r)
        display.line(tip[0], tip[1], hx, hy)


def render(display, weather, stale_marker=None, invert=None):
    try:
        display.set_update_speed(0)
    except Exception:
        pass

    w = weather or {}
    if invert is None:
        invert = _is_night_hour(w.get("updated_hour_local"))

    bg = BLACK if invert else WHITE
    fg = WHITE if invert else BLACK

    display.set_pen(bg)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(fg)

    temp = w.get("temp_f")
    cat = w.get("flight_category") or "--"
    station = w.get("station") or "----"
    station_name = w.get("station_name")
    wind = w.get("wind") or "--"
    wind_deg = w.get("wind_deg")
    sky = w.get("summary") or "--"
    vis = w.get("visibility_sm")
    updated = w.get("updated_z")
    dewp = w.get("dewpoint_f")
    da = w.get("density_altitude_ft")
    sr = w.get("sunrise_local")
    ss = w.get("sunset_local")
    hw = w.get("headwind_kt")
    xw = w.get("crosswind_kt")
    xw_side = w.get("crosswind_side")

    display.set_font("bitmap8")

    # Big temp top-left.
    temp_str = "{0}F".format(int(temp)) if temp is not None else "--F"
    display.text(temp_str, 8, 10, scale=_CAT_SCALE)

    # Big flight category top-right — inverted block for degraded conditions.
    # (If night-mode is already inverting the whole screen, skip the sub-invert.)
    cat_w = len(cat) * _CAT_CHAR_W
    cat_x = WIDTH - cat_w - 8
    if cat in ("IFR", "LIFR") and not invert:
        display.set_pen(fg)
        display.rectangle(cat_x - 6, 4, cat_w + 12, 52)
        display.set_pen(bg)
        display.text(cat, cat_x, 10, scale=_CAT_SCALE)
        display.set_pen(fg)
    else:
        display.text(cat, cat_x, 10, scale=_CAT_SCALE)

    # Wind rose arrow between temp and category.
    _draw_wind_arrow(display, 148, 28, 14, wind_deg)

    # Top annotation row: station name left, last-updated right.
    if station_name:
        display.text(station_name, 8, 54, scale=1)
    if updated is not None:
        stamp = "last updated {0}Z".format(updated)
        stamp_x = WIDTH - (len(stamp) * 6) - 6
        display.text(stamp, stamp_x, 54, scale=1)

    # Divider.
    display.line(0, 64, WIDTH, 64)

    # Station / visibility / DA.
    line1 = station
    if vis is not None:
        if vis == int(vis):
            line1 += "  vis {0}SM".format(int(vis))
        else:
            line1 += "  vis {0}SM".format(vis)
    if da is not None:
        line1 += "  DA{0}".format(da)
    display.text(line1, 8, 72, scale=2)

    # Wind line + temp/dew pair.
    wind_line = wind
    if temp is not None and dewp is not None:
        wind_line += "  {0}/{1}".format(int(temp), int(dewp))
    display.text(wind_line, 8, 90, scale=2)

    # Clouds line.
    display.text(sky, 8, 108, scale=2)

    # Bottom-left small line: runway readout (when configured).
    rwy_hdg = w.get("runway_heading_deg")
    if rwy_hdg is not None and hw is not None and xw is not None:
        rwy_num = int(round(rwy_hdg / 10.0)) % 36
        if rwy_num == 0:
            rwy_num = 36
        rwy_line = "RWY {0:02d}  HW {1}  XW {2}{3}".format(
            rwy_num, hw, xw, xw_side or "")
        display.text(rwy_line, 8, HEIGHT - 9, scale=1)

    # Bottom-right small line: sunrise / sunset.
    if sr is not None or ss is not None:
        parts = []
        if sr is not None:
            parts.append("SR {0}".format(sr))
        if ss is not None:
            parts.append("SS {0}".format(ss))
        line = "  ".join(parts)
        display.text(line, WIDTH - (len(line) * 6) - 6, HEIGHT - 9, scale=1)

    if stale_marker:
        # Stale marker pre-empts the runway slot if both compete for the
        # bottom-left.
        display.text(stale_marker, 8, HEIGHT - 9, scale=1)

    display.update()
