WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128

_MAX_VISIBLE = 5
_ROW_H = 20


def _clear_white(display):
    display.set_pen(WHITE)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(BLACK)


def _window(total, cursor):
    if total <= _MAX_VISIBLE:
        return 0
    start = cursor - _MAX_VISIBLE // 2
    if start < 0:
        return 0
    if start + _MAX_VISIBLE > total:
        return total - _MAX_VISIBLE
    return start


def render(display, stations, cursor, active_index):
    _clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    display.text("ICAO picker", 8, 4, scale=1)
    display.text("A select   B back", WIDTH - 110, 4, scale=1)
    display.line(0, 14, WIDTH, 14)

    total = len(stations)
    start = _window(total, cursor)
    end = min(start + _MAX_VISIBLE, total)

    for i in range(start, end):
        y = 20 + (i - start) * _ROW_H
        prefix = ">" if i == cursor else " "
        suffix = " *" if i == active_index else ""
        display.text("{0} {1}{2}".format(prefix, stations[i], suffix), 8, y, scale=2)

    if total > _MAX_VISIBLE:
        display.text("{0}/{1}".format(cursor + 1, total), WIDTH - 40, HEIGHT - 10, scale=1)

    display.update()
