class FakeDisplay:
    WIDTH = 296
    HEIGHT = 128

    def __init__(self):
        self.calls: list[tuple] = []
        self._pressed: set[str] = set()

    def _log(self, name, *args):
        self.calls.append((name, args))

    def press(self, btn):
        self._pressed.add(btn)

    def release(self, btn):
        self._pressed.discard(btn)

    def clear(self):
        self._log("clear")

    def update(self):
        self._log("update")

    def halt(self):
        self._log("halt")

    def set_pen(self, v):
        self._log("set_pen", v)

    def set_font(self, name):
        self._log("set_font", name)

    def text(self, s, x, y, wordwrap=None, scale=1.0):
        self._log("text", s, x, y, wordwrap, scale)

    def rectangle(self, x, y, w, h):
        self._log("rectangle", x, y, w, h)

    def line(self, x1, y1, x2, y2):
        self._log("line", x1, y1, x2, y2)

    def pixel(self, x, y):
        self._log("pixel", x, y)

    def image(self, buf, w, h, x, y):
        self._log("image", len(buf) if hasattr(buf, "__len__") else None, w, h, x, y)

    def led(self, v):
        self._log("led", v)

    def pressed(self, btn):
        return btn in self._pressed

    def texts(self):
        return [args[0] for name, args in self.calls if name == "text"]
