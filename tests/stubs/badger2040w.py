BUTTON_A = "A"
BUTTON_B = "B"
BUTTON_C = "C"
BUTTON_UP = "UP"
BUTTON_DOWN = "DOWN"

WIDTH = 296
HEIGHT = 128


class Badger2040W:
    def __init__(self):
        self._pressed = set()

    def clear(self):
        pass

    def update(self):
        pass

    def halt(self):
        pass

    def set_pen(self, v):
        pass

    def set_font(self, name):
        pass

    def text(self, s, x, y, wordwrap=None, scale=1.0):
        pass

    def rectangle(self, x, y, w, h):
        pass

    def line(self, x1, y1, x2, y2):
        pass

    def pixel(self, x, y):
        pass

    def image(self, buf, w, h, x, y):
        pass

    def led(self, v):
        pass

    def pressed(self, btn):
        return btn in self._pressed
