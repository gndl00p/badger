from screens.common import BLACK, HEIGHT, WIDTH, clear_white, draw_qr


def _load_image(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return bytes(128 * 128 // 8)


def render(display, config, headshot_path="assets/headshot.bin"):
    clear_white(display)

    buf = _load_image(headshot_path)
    display.image(buf, 128, 128, 0, 0)

    display.set_pen(BLACK)
    display.set_font("bitmap14_outline")
    display.text(config.NAME, 136, 10, scale=1.2)

    display.set_font("bitmap8")
    display.text(config.TITLE, 136, 38, scale=1.0)
    display.text(config.ORG, 136, 56, scale=1.0)

    draw_qr(display, config.URL, x=WIDTH - 64, y=HEIGHT - 64, size_px=60)

    display.update()