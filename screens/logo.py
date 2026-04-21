from screens.common import HEIGHT, WIDTH, clear_white


def _load_image(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return bytes(WIDTH * HEIGHT // 8)


def render(display, config, wordmark_path="assets/robbtech_wordmark.bin"):
    clear_white(display)
    buf = _load_image(wordmark_path)
    display.image(buf, WIDTH, HEIGHT, 0, 0)
    display.update()