from screens.common import BLACK, clear_white, draw_header_rule, wrap

_LINE_H = 16
_WRAP_CHARS = 28


def render(display, config):
    clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    display.text("Now", 4, 4, scale=1.4)
    draw_header_rule(display, y=24)

    y = 34
    for line in wrap(config.NOW, _WRAP_CHARS):
        display.text(line, 4, y, scale=1.2)
        y += _LINE_H

    display.update()