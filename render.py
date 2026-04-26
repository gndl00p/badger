WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128

_CAT_CHAR_W = 30  # bitmap8 char at scale 5


def render(display, weather, stale_marker=None, invert=None):
    try:
        display.set_update_speed(0)
    except Exception:
        pass

    w = weather or {}
    if invert is None:
        invert = False
    bg = BLACK if invert else WHITE
    fg = WHITE if invert else BLACK

    display.set_pen(bg)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(fg)
    display.set_font("bitmap8")

    # ─── Header strip (scale 1) ──────────────────────────────
    station = w.get("station") or "----"
    name = w.get("station_name") or ""
    updated = w.get("updated_z")

    head = "{0} {1}".format(station, name).strip()
    display.text(head, 4, 2, scale=1)
    if updated is not None:
        right = "{0}Z".format(updated)
        display.text(right, WIDTH - len(right) * 6 - 4, 2, scale=1)
    display.line(0, 12, WIDTH, 12)

    # ─── Hero (scale 5) ──────────────────────────────────────
    temp = w.get("temp_f")
    cat = w.get("flight_category") or "--"
    temp_str = "{0}F".format(int(temp)) if temp is not None else "--F"
    display.text(temp_str, 12, 18, scale=5)

    cat_w = len(cat) * _CAT_CHAR_W
    cat_x = WIDTH - cat_w - 12
    if cat in ("IFR", "LIFR") and not invert:
        display.set_pen(fg)
        display.rectangle(cat_x - 8, 14, cat_w + 16, 50)
        display.set_pen(bg)
        display.text(cat, cat_x, 18, scale=5)
        display.set_pen(fg)
    else:
        display.text(cat, cat_x, 18, scale=5)

    display.line(0, 62, WIDTH, 62)

    # ─── Body (scale 2, 3 readable rows) ─────────────────────
    wind = w.get("wind") or "--"
    vis = w.get("visibility_sm")
    da = w.get("density_altitude_ft")
    dewp = w.get("dewpoint_f")
    sky = w.get("summary") or "--"
    ceiling = w.get("ceiling_ft")

    # Row 1: wind + temp/dew pair
    line1 = "WIND {0}".format(wind)
    if temp is not None and dewp is not None:
        line1 += "  {0}/{1}".format(int(temp), int(dewp))
    display.text(line1, 4, 66, scale=2)

    # Row 2: clouds + visibility
    line2 = "CLD {0}".format(sky)
    if vis is not None:
        v = int(vis) if vis == int(vis) else vis
        line2 += "  vis {0}SM".format(v)
    display.text(line2, 4, 84, scale=2)

    # Row 3: aviation pressure block — altimeter, DA, ceiling.
    altim = w.get("altimeter_inhg")
    parts3 = []
    if altim is not None:
        parts3.append("ALT {0:.2f}".format(altim))
    if da is not None:
        parts3.append("DA {0}".format(da))
    if ceiling is not None:
        parts3.append("CEIL {0}".format(ceiling))
    if not parts3:
        parts3.append("---")
    display.text("  ".join(parts3), 4, 102, scale=2)

    if stale_marker:
        display.text(stale_marker, 4, 120, scale=1)

    display.update()
