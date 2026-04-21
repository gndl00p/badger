from types import SimpleNamespace
from unittest.mock import MagicMock

from tests.fakes.display import FakeDisplay

import modes.badge as badge


def _cfg():
    return SimpleNamespace(
        NAME="Philip", TITLE="T", ORG="R", URL="https://robb.tech",
        CONTACT={"email": "a@b"}, BIO="bio", BIO_SKILLS="py", NOW="now",
    )


def _stub_screens(monkeypatch):
    stubs = []
    for attr in ("name_card", "contact", "bio", "now", "logo"):
        m = MagicMock()
        monkeypatch.setattr(badge, attr, SimpleNamespace(render=m))
        stubs.append(m)
    return stubs


def test_boots_on_screen_zero(monkeypatch):
    stubs = _stub_screens(monkeypatch)
    d = FakeDisplay()

    controller = badge.BadgeMode(d, _cfg(), screen_index=0)
    controller.render_current()

    stubs[0].assert_called_once()
    for s in stubs[1:]:
        s.assert_not_called()


def test_c_advances_to_next(monkeypatch):
    stubs = _stub_screens(monkeypatch)
    d = FakeDisplay()
    controller = badge.BadgeMode(d, _cfg(), screen_index=0)

    controller.handle_button("C")
    stubs[1].assert_called_once()
    assert controller.screen_index == 1


def test_a_goes_to_previous_wrapping(monkeypatch):
    stubs = _stub_screens(monkeypatch)
    d = FakeDisplay()
    controller = badge.BadgeMode(d, _cfg(), screen_index=0)

    controller.handle_button("A")
    stubs[4].assert_called_once()
    assert controller.screen_index == 4


def test_c_wraps_from_last_to_first(monkeypatch):
    stubs = _stub_screens(monkeypatch)
    d = FakeDisplay()
    controller = badge.BadgeMode(d, _cfg(), screen_index=4)

    controller.handle_button("C")
    stubs[0].assert_called_once()
    assert controller.screen_index == 0


def test_b_redraws(monkeypatch):
    stubs = _stub_screens(monkeypatch)
    d = FakeDisplay()
    controller = badge.BadgeMode(d, _cfg(), screen_index=2)

    controller.handle_button("B")
    assert stubs[2].call_count == 1
    assert controller.screen_index == 2


def test_up_toggles_led(monkeypatch):
    _stub_screens(monkeypatch)
    d = FakeDisplay()
    controller = badge.BadgeMode(d, _cfg(), screen_index=0)

    controller.handle_button("UP")
    controller.handle_button("UP")
    led_values = [args[0] for name, args in d.calls if name == "led"]
    assert led_values == [255, 0]


def test_down_halts(monkeypatch):
    _stub_screens(monkeypatch)
    d = FakeDisplay()
    controller = badge.BadgeMode(d, _cfg(), screen_index=0)

    controller.handle_button("DOWN")
    assert ("halt", ()) in d.calls