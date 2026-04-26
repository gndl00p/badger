WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128


def render(display, version="v0.3.0"):
    try:
        display.set_update_speed(0)
    except Exception:
        pass

    display.set_pen(WHITE)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    display.text("SkyGlance", 40, 28, scale=5)

    # Subtitle
    sub = "aviation weather"
    sub_x = (WIDTH - len(sub) * 12) // 2
    display.text(sub, sub_x, 82, scale=2)

    # Version in the corner
    display.text(version, WIDTH - len(version) * 6 - 6, HEIGHT - 10, scale=1)

    # A simple horizontal rule under the title
    display.line(40, 72, WIDTH - 40, 72)

    display.update()
