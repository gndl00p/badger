WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128


def _clear_white(display):
    display.set_pen(WHITE)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(BLACK)


def render(display, weather, stale_marker=None):
    # UPDATE_NORMAL == 0 — cleanest refresh for the main weather view.
    try:
        display.set_update_speed(0)
    except Exception:
        pass

    _clear_white(display)
    display.set_pen(BLACK)

    w = weather or {}
    temp = w.get("temp_f")
    cat = w.get("flight_category") or "--"
    station = w.get("station") or "----"
    wind = w.get("wind") or "--"
    sky = w.get("summary") or "--"
    vis = w.get("visibility_sm")
    updated = w.get("updated_z")

    display.set_font("bitmap8")

    temp_str = "{0}F".format(int(temp)) if temp is not None else "--F"
    display.text(temp_str, 8, 10, scale=5)

    cat_x = WIDTH - (len(cat) * 30) - 8
    display.text(cat, cat_x, 10, scale=5)

    if updated is not None:
        stamp = "last updated {0}Z".format(updated)
        stamp_x = WIDTH - (len(stamp) * 6) - 6
        display.text(stamp, stamp_x, 54, scale=1)

    display.line(0, 64, WIDTH, 64)

    line1 = station
    if vis is not None:
        if vis == int(vis):
            line1 += "  vis {0}SM".format(int(vis))
        else:
            line1 += "  vis {0}SM".format(vis)
    da = w.get("density_altitude_ft")
    if da is not None:
        line1 += "  DA{0}".format(da)
    display.text(line1, 8, 72, scale=2)

    display.text(wind, 8, 90, scale=2)

    display.text(sky, 8, 108, scale=2)

    if stale_marker:
        display.text(stale_marker, WIDTH - 56, HEIGHT - 8, scale=1)

    display.update()
