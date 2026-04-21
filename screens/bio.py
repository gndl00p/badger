from screens.common import BLACK, clear_white, draw_header_rule, wrap

_LINE_H = 14
_WRAP_CHARS = 36


def render(display, config):
    clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    display.text("About", 4, 4, scale=1.2)
    draw_header_rule(display, y=22)

    y = 28
    for line in wrap(config.BIO, _WRAP_CHARS):
        display.text(line, 4, y, scale=1.0)
        y += _LINE_H

    y += 4
    display.text("Skills:", 4, y, scale=1.0)
    y += _LINE_H
    display.text(config.BIO_SKILLS, 4, y, scale=0.9)

    display.update()