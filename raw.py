WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128

_WRAP_CHARS = 24
_LINE_H = 12


def _clear_white(display):
    display.set_pen(WHITE)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(BLACK)


def _wrap(text, max_chars):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur = cur + " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(display, weather):
    # UPDATE_NORMAL for text legibility.
    try:
        display.set_update_speed(0)
    except Exception:
        pass

    _clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    display.text("Details", 8, 4, scale=2)
    display.text("B back", WIDTH - 60, 8, scale=1)
    display.line(0, 24, WIDTH, 24)

    w = weather or {}
    y = 30

    altim = w.get("altimeter_inhg")
    dew = w.get("dewpoint_f")
    spread = w.get("spread_f")
    da = w.get("density_altitude_ft")
    pa = w.get("pressure_altitude_ft")

    parts = []
    if altim is not None:
        parts.append("ALT {0:.2f}".format(altim))
    if dew is not None:
        parts.append("DEW {0}F".format(dew))
    if spread is not None:
        parts.append("SPD {0}F".format(spread))
    if parts:
        display.text("   ".join(parts), 8, y, scale=1)
        y += 14

    parts2 = []
    if da is not None:
        parts2.append("DA {0}".format(da))
    if pa is not None:
        parts2.append("PA {0}".format(pa))
    if parts2:
        display.text("   ".join(parts2), 8, y, scale=1)
        y += 14

    raw_text = w.get("raw")
    if not raw_text:
        display.text("(no raw METAR yet)", 8, y, scale=1)
        display.update()
        return

    display.text("raw METAR:", 8, y, scale=1)
    y += 12
    lines = _wrap(raw_text, _WRAP_CHARS)
    for line in lines[:5]:
        display.text(line, 8, y, scale=1)
        y += _LINE_H
    if len(lines) > 5:
        display.text("(+{0} more)".format(len(lines) - 5), WIDTH - 80, HEIGHT - 10, scale=1)

    display.update()
