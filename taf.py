WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128

_WRAP_CHARS = 49
_LINE_H = 10


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


def render(display, raw_taf, station=None):
    # UPDATE_NORMAL for text legibility.
    try:
        display.set_update_speed(0)
    except Exception:
        pass

    _clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    title = "TAF  {0}".format(station) if station else "TAF"
    display.text(title, 8, 4, scale=2)
    display.text("B back", WIDTH - 60, 8, scale=1)
    display.line(0, 24, WIDTH, 24)

    if not raw_taf:
        display.text("no TAF available", 8, 40, scale=2)
        display.update()
        return

    y = 30
    # TAF bodies are long — use small text so more fits on screen.
    lines = _wrap(raw_taf, _WRAP_CHARS)
    max_visible = (HEIGHT - y - 10) // _LINE_H
    for line in lines[:max_visible]:
        display.text(line, 8, y, scale=1)
        y += _LINE_H

    if len(lines) > max_visible:
        display.text("(+{0} more)".format(len(lines) - max_visible),
                     WIDTH - 80, HEIGHT - 9, scale=1)

    display.update()
