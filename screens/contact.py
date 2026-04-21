from screens.common import BLACK, HEIGHT, clear_white, draw_qr

_QR_SIZE = 40
_ROW_H = 44


def render(display, config):
    clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    items = list(config.CONTACT.items())[:3]  # 3 rows fit at 44 px each
    for idx, (label, value) in enumerate(items):
        y = idx * _ROW_H + 4
        display.text(label, 4, y, scale=1.0)
        display.text(value, 4, y + 16, scale=0.9)
        draw_qr(display, value, x=256, y=y, size_px=_QR_SIZE)

    display.update()