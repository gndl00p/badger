from screens import bio, contact, logo, name_card, now  # noqa: F401

_SCREEN_NAMES = ("name_card", "contact", "bio", "now", "logo")
_COUNT = len(_SCREEN_NAMES)


class BadgeMode:
    def __init__(self, display, config, screen_index=0):
        self.display = display
        self.config = config
        self.screen_index = screen_index % _COUNT
        self._led_on = False

    def render_current(self):
        screen = globals()[_SCREEN_NAMES[self.screen_index]]
        screen.render(self.display, self.config)

    def handle_button(self, btn):
        if btn == "A":
            self.screen_index = (self.screen_index - 1) % _COUNT
            self.render_current()
        elif btn == "C":
            self.screen_index = (self.screen_index + 1) % _COUNT
            self.render_current()
        elif btn == "B":
            self.render_current()
        elif btn == "UP":
            self._led_on = not self._led_on
            self.display.led(255 if self._led_on else 0)
        elif btn == "DOWN":
            self.display.halt()
