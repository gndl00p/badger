try:
    import badger2040
except ImportError:
    badger2040 = None

try:
    import machine
except ImportError:
    machine = None

import time

from modes.badge import BadgeMode
from modes.desk import DeskMode
from badge_state import load as load_state
from mode_switch import transition


_BUTTONS = (
    ("BUTTON_A", "A"),
    ("BUTTON_B", "B"),
    ("BUTTON_C", "C"),
    ("BUTTON_UP", "UP"),
    ("BUTTON_DOWN", "DOWN"),
)

_LONG_PRESS_SECONDS = 2.0
_POLL_INTERVAL = 0.05


def _wake_button():
    if badger2040 is None:
        return None
    if not badger2040.woken_by_button():
        return None
    for const_name, label in _BUTTONS:
        const = getattr(badger2040, const_name, None)
        if const is not None and badger2040.pressed_to_wake(const):
            return label
    return None


def _pressed_label(display):
    if badger2040 is None:
        return None
    for const_name, label in _BUTTONS:
        const = getattr(badger2040, const_name, None)
        if const is not None and display.pressed(const):
            return label
    return None


def _announce_mode_switch(display, new_mode):
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display.set_font("bitmap8")
    display.text("switching to", 10, 40, scale=1.4)
    display.text(new_mode, 10, 72, scale=1.8)
    display.update()


def _handle_long_press_b(display, state_path):
    start = time.time()
    btn_b = getattr(badger2040, "BUTTON_B", None)
    while display.pressed(btn_b):
        if time.time() - start >= _LONG_PRESS_SECONDS:
            new_mode = transition(state_path)
            _announce_mode_switch(display, new_mode)
            if machine is not None:
                machine.reset()
            return True
        time.sleep(_POLL_INTERVAL)
    return False


def _wait_for_release(display, label):
    for const_name, lbl in _BUTTONS:
        if lbl == label:
            const = getattr(badger2040, const_name, None)
            while const is not None and display.pressed(const):
                time.sleep(_POLL_INTERVAL)
            return


def _build_display():
    return badger2040.Badger2040()


def _load_config():
    import config
    return config


def _poll_loop(display, on_button, state_path):
    while True:
        label = _pressed_label(display)
        if label is None:
            time.sleep(_POLL_INTERVAL)
            continue
        if label == "B":
            if _handle_long_press_b(display, state_path):
                return
        on_button(label)
        _wait_for_release(display, label)


def run(state_path="/state.json"):
    state = load_state(state_path)
    mode = state.get("mode", "badge")
    display = _build_display()
    config = _load_config()

    btn = _wake_button()

    if btn == "B" and badger2040 is not None:
        if _handle_long_press_b(display, state_path):
            return

    if mode == "desk":
        controller = DeskMode(display, config, state_path=state_path)
        if btn == "A":
            controller.handle_button("A")
        else:
            controller.cycle()
        _poll_loop(display, controller.handle_button, state_path)
    else:
        controller = BadgeMode(display, config)
        if btn in ("A", "B", "C", "UP", "DOWN"):
            controller.handle_button(btn)
        else:
            controller.render_current()
        _poll_loop(display, controller.handle_button, state_path)


if __name__ == "__main__":
    run()
