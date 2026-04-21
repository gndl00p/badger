class QRCode:
    def __init__(self):
        self._text = ""

    def set_text(self, s):
        self._text = s

    def get_size(self):
        return (21, 21)

    def get_module(self, x, y):
        return ((x + y) % 2) == 0
