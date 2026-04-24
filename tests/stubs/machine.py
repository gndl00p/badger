def deepsleep(ms):
    pass


def reset():
    pass


class Pin:
    IN = 0
    OUT = 1

    def __init__(self, *a, **kw):
        pass

    def value(self, v=None):
        return 0


class ADC:
    def __init__(self, channel):
        self.channel = channel

    def read_u16(self):
        return 0
