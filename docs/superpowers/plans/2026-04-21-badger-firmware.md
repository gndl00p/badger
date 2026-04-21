# Badger 2040 W Firmware + Host Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the dual-mode MicroPython firmware for the Badger 2040 W — Badge mode (5-screen name-card deck, Wi-Fi off, battery) and Desk mode (single 4-tile dashboard pulling from the aggregator, Wi-Fi on, USB) — plus the host-side tools needed to produce assets and flash the device.

**Architecture:** Pure-logic modules (screens, mode controllers, state persistence, long-press detection, dashboard renderer, desk fetcher) take injected `display` / `wifi` / `http` objects so they can be unit-tested on the host with stub implementations of Pimoroni's `badger2040w`, plus `network`, `urequests`, `machine`, `ujson`. `main.py` on the device wires real device objects in; host tests wire fakes. State (`{"mode": ..., "last_data": ...}`) persists in `/state.json` on the device filesystem.

**Tech Stack:** MicroPython (Pimoroni Badger 2040 W build), `badger2040w`, `jpegdec`, `qrcode`, `network`, `urequests`, `ujson`, `machine`. Host tools: Python 3.11+, Pillow, numpy, pytest. Flash: `mpremote`.

**Prerequisites:** Aggregator plan (`2026-04-21-badger-aggregator-service.md`) not required to be complete for firmware development — desk mode's tests stub the HTTP layer. Only the live on-device smoke test (Task 19) requires the aggregator to be reachable.

---

## File Structure

Created / populated (all paths relative to `~/code/badger/`):

| File | Responsibility |
| --- | --- |
| `.gitignore` | Ignore venv, `.env`, `__pycache__` |
| `main.py` | Device entry — load state, dispatch to mode, handle long-press |
| `config.example.py` | Template config (Philip's fields + Wi-Fi + aggregator URL/token) |
| `state.py` | Read/write `/state.json` with defaults; pure Python, device+host |
| `mode_switch.py` | Long-press B detection + persisted mode transition |
| `modes/__init__.py` | Marks package |
| `modes/badge.py` | Badge-mode controller: screen deck nav, button bindings, halt |
| `modes/desk.py` | Desk-mode controller: connect, fetch, render, deepsleep |
| `screens/__init__.py` | Marks package |
| `screens/common.py` | Shared drawing helpers: header rule, wrap, QR render |
| `screens/name_card.py` | Screen 1 |
| `screens/contact.py` | Screen 2 |
| `screens/bio.py` | Screen 3 |
| `screens/now.py` | Screen 4 |
| `screens/logo.py` | Screen 5 |
| `desk/__init__.py` | Marks package |
| `desk/fetcher.py` | Wi-Fi connect + HTTP GET + stale fallback |
| `desk/render.py` | 4-tile dashboard layout |
| `assets/headshot.bin` | 128×128 1-bit packed (placeholder until source PNG provided) |
| `assets/robbtech_wordmark.bin` | 296×128 1-bit packed (placeholder) |
| `tools/dither_image.py` | Host tool: PNG/JPG → 1-bit `.bin` |
| `tools/make_placeholder_assets.py` | Generates placeholder headshot + wordmark bins |
| `tools/flash.sh` | `mpremote cp` wrapper for firmware + assets |
| `tests/__init__.py` | Marks package |
| `tests/conftest.py` | Adds `tests/stubs` to `sys.path` |
| `tests/stubs/badger2040w.py` | Stub Badger2040W API |
| `tests/stubs/network.py` | Stub `WLAN` |
| `tests/stubs/urequests.py` | Stub `get()` |
| `tests/stubs/machine.py` | Stub `deepsleep`, `reset`, `Pin` |
| `tests/stubs/ujson.py` | Re-export `json` |
| `tests/stubs/qrcode.py` | Stub `QRCode` |
| `tests/stubs/jpegdec.py` | Stub `JPEG` |
| `tests/fakes/display.py` | `FakeDisplay` recording draw calls |
| `tests/test_state.py` | `state.py` round-trip |
| `tests/test_screens_name_card.py` | Name-card render assertions |
| `tests/test_screens_contact.py` | Contact render assertions |
| `tests/test_screens_bio.py` | Bio render assertions |
| `tests/test_screens_now.py` | Now render assertions |
| `tests/test_screens_logo.py` | Logo render assertions |
| `tests/test_modes_badge.py` | Screen deck nav + button dispatch |
| `tests/test_desk_fetcher.py` | Wi-Fi + HTTP + stale fallback |
| `tests/test_desk_render.py` | 4-tile layout |
| `tests/test_modes_desk.py` | End-to-end desk cycle with fakes |
| `tests/test_mode_switch.py` | Long-press detection + persistence |
| `tests/test_tools_dither.py` | Dither tool round-trip |
| `pyproject.toml` | Host dev deps + pytest config |

---

## Task 1: Repo scaffolding

**Files:**
- Create: `.gitignore`
- Create: `main.py` (stub)
- Create: `config.example.py`
- Create: `state.json`
- Create: `modes/__init__.py`
- Create: `screens/__init__.py`
- Create: `desk/__init__.py`
- Create: `tools/` directory marker (no `__init__.py`; not a package)
- Create: `tests/__init__.py`
- Create: `pyproject.toml`

- [ ] **Step 1: Write `.gitignore`**

```
.venv/
server/.venv/
server/.env
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 2: Write `config.example.py`**

```python
# Copy to config.py on the device (or deploy via tools/flash.sh).
NAME = "Philip Robb"
TITLE = "Technical Lead"
ORG = "Robb.Tech"
URL = "https://robb.tech"
CONTACT = {
    "email": "philip@teamrobb.com",
    "linkedin": "https://www.linkedin.com/in/philip-robb",
}
BIO = "Technical lead building infrastructure and automation at Robb.Tech."
BIO_SKILLS = "Python · Linux · networks · LLMs"
NOW = "Building out the Robb.Tech platform."

WIFI_SSID = "REPLACE-ME"
WIFI_PSK = "REPLACE-ME"

AGGREGATOR_URL = "http://endevour.robb.tech:8088/badge.json"
AGGREGATOR_TOKEN = "REPLACE-ME"
REFRESH_MINUTES = 15
```

- [ ] **Step 3: Write `state.json`** (empty default)

```
{}
```

- [ ] **Step 4: Write `main.py`** stub (will be fleshed out in Task 15)

```python
# Device entry point. Filled in by Task 15.
```

- [ ] **Step 5: Create empty package markers**

```bash
cd ~/code/badger
touch modes/__init__.py screens/__init__.py desk/__init__.py tests/__init__.py
mkdir -p tools tests/stubs tests/fakes
touch tests/stubs/__init__.py tests/fakes/__init__.py
```

- [ ] **Step 6: Write `pyproject.toml`** (host dev deps)

```toml
[project]
name = "badger-firmware-host-tools"
version = "0.0.0"
requires-python = ">=3.11"

[project.optional-dependencies]
dev = [
    "pytest==8.3.3",
    "Pillow==11.0.0",
    "numpy==2.1.3",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 7: Create host venv and install dev deps**

Run:
```bash
cd ~/code/badger
python3 -m venv .venv
.venv/bin/pip install pytest==8.3.3 Pillow==11.0.0 numpy==2.1.3
.venv/bin/pytest tests -v
```
Expected: `no tests ran in 0.00s`, exit 0. `pyproject.toml` is auto-detected by pytest and supplies `testpaths` / `pythonpath`. The `optional-dependencies` block is documentation of pinned versions; an editable install (`pip install -e '.[dev]'`) is not used because the project has no `[build-system]` table.

- [ ] **Step 8: Commit**

```bash
cd ~/code/badger
git add .gitignore main.py config.example.py state.json \
        modes/__init__.py screens/__init__.py desk/__init__.py \
        tests/__init__.py tests/stubs/__init__.py tests/fakes/__init__.py \
        pyproject.toml
git commit -m "chore: scaffold firmware package and host dev environment"
```

---

## Task 2: Host stubs for MicroPython-only modules

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/stubs/badger2040w.py`
- Create: `tests/stubs/network.py`
- Create: `tests/stubs/urequests.py`
- Create: `tests/stubs/machine.py`
- Create: `tests/stubs/ujson.py`
- Create: `tests/stubs/qrcode.py`
- Create: `tests/stubs/jpegdec.py`
- Create: `tests/fakes/display.py`

- [ ] **Step 1: Write `tests/conftest.py`**

```python
import sys
from pathlib import Path

_STUBS = Path(__file__).parent / "stubs"
if str(_STUBS) not in sys.path:
    sys.path.insert(0, str(_STUBS))
```

- [ ] **Step 2: Write `tests/stubs/badger2040w.py`**

```python
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
```

- [ ] **Step 3: Write `tests/stubs/network.py`**

```python
STA_IF = 0


class WLAN:
    def __init__(self, iface):
        self._active = False
        self._connected = False

    def active(self, v=None):
        if v is not None:
            self._active = v
        return self._active

    def connect(self, ssid, psk):
        self._connected = True

    def isconnected(self):
        return self._connected

    def disconnect(self):
        self._connected = False
```

- [ ] **Step 4: Write `tests/stubs/urequests.py`**

```python
class Response:
    def __init__(self, status_code=200, json_body=None, text=""):
        self.status_code = status_code
        self._json = json_body
        self.text = text

    def json(self):
        return self._json

    def close(self):
        pass


def get(url, headers=None, timeout=None):
    raise NotImplementedError("patch urequests.get in tests")
```

- [ ] **Step 5: Write `tests/stubs/machine.py`**

```python
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
```

- [ ] **Step 6: Write `tests/stubs/ujson.py`**

```python
from json import dumps, loads  # noqa: F401
```

- [ ] **Step 7: Write `tests/stubs/qrcode.py`**

```python
class QRCode:
    def __init__(self):
        self._text = ""

    def set_text(self, s):
        self._text = s

    def get_size(self):
        return (21, 21)

    def get_module(self, x, y):
        return ((x + y) % 2) == 0
```

- [ ] **Step 8: Write `tests/stubs/jpegdec.py`**

```python
class JPEG:
    def __init__(self, display):
        self.display = display

    def open_file(self, path):
        pass

    def decode(self, x=0, y=0, scale=0, dither=False):
        pass
```

- [ ] **Step 9: Write `tests/fakes/display.py`**

```python
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
```

- [ ] **Step 10: Verify stubs import cleanly**

Run: `cd ~/code/badger && python -c "import sys; sys.path.insert(0, 'tests/stubs'); import badger2040w, network, urequests, machine, ujson, qrcode, jpegdec; print('ok')"`
Expected: `ok`.

- [ ] **Step 11: Commit**

```bash
git add tests/conftest.py tests/stubs/*.py tests/fakes/*.py
git commit -m "test: host stubs for MicroPython-only modules"
```

---

## Task 3: `state.py` — state.json read/write

**Files:**
- Create: `state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Write `tests/test_state.py`**

```python
from pathlib import Path

import state


def test_load_missing_returns_defaults(tmp_path):
    p = tmp_path / "state.json"
    assert state.load(str(p)) == {"mode": "badge", "last_data": None}


def test_load_empty_file_returns_defaults(tmp_path):
    p = tmp_path / "state.json"
    p.write_text("")
    assert state.load(str(p)) == {"mode": "badge", "last_data": None}


def test_load_bad_json_returns_defaults(tmp_path):
    p = tmp_path / "state.json"
    p.write_text("{not json")
    assert state.load(str(p)) == {"mode": "badge", "last_data": None}


def test_round_trip(tmp_path):
    p = tmp_path / "state.json"
    payload = {"mode": "desk", "last_data": {"weather": {"temp_f": 70}}}
    state.save(str(p), payload)
    assert state.load(str(p)) == payload


def test_save_overwrites(tmp_path):
    p = tmp_path / "state.json"
    state.save(str(p), {"mode": "badge", "last_data": None})
    state.save(str(p), {"mode": "desk", "last_data": None})
    assert state.load(str(p))["mode"] == "desk"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_state.py -v`
Expected: 5 failures with `ModuleNotFoundError: No module named 'state'`.

- [ ] **Step 3: Write `state.py`**

```python
try:
    import ujson as _json  # MicroPython
except ImportError:
    import json as _json  # CPython host

_DEFAULT = {"mode": "badge", "last_data": None}


def load(path):
    try:
        with open(path, "r") as f:
            raw = f.read()
        if not raw.strip():
            return dict(_DEFAULT)
        return _json.loads(raw)
    except (OSError, ValueError):
        return dict(_DEFAULT)


def save(path, data):
    with open(path, "w") as f:
        f.write(_json.dumps(data))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_state.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add state.py tests/test_state.py
git commit -m "feat: state.py read/write state.json with defaults"
```

---

## Task 4: `screens/common.py` — shared drawing helpers

**Files:**
- Create: `screens/common.py`
- Test: `tests/test_screens_common.py`

- [ ] **Step 1: Write `tests/test_screens_common.py`**

```python
from tests.fakes.display import FakeDisplay

import screens.common as common


def test_clear_white_fills_background():
    d = FakeDisplay()
    common.clear_white(d)
    assert ("set_pen", (15,)) in d.calls
    assert any(name == "rectangle" for name, _ in d.calls)
    assert ("set_pen", (0,)) in d.calls


def test_draw_qr_renders_modules():
    d = FakeDisplay()
    common.draw_qr(d, "https://robb.tech", x=200, y=30, size_px=60)
    pixel_calls = [args for name, args in d.calls if name == "rectangle" or name == "pixel"]
    assert len(pixel_calls) > 0


def test_draw_header_rule():
    d = FakeDisplay()
    common.draw_header_rule(d, y=20)
    line_calls = [args for name, args in d.calls if name == "line"]
    assert line_calls == [(0, 20, 296, 20)]


def test_wrap_text_into_lines():
    lines = common.wrap("one two three four five", max_chars=8)
    assert lines == ["one two", "three", "four", "five"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_screens_common.py -v`
Expected: failures with `ModuleNotFoundError: No module named 'screens.common'`.

- [ ] **Step 3: Write `screens/common.py`**

```python
try:
    import qrcode
except ImportError:
    qrcode = None


WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128


def clear_white(display):
    display.set_pen(WHITE)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(BLACK)


def draw_header_rule(display, y=20):
    display.line(0, y, WIDTH, y)


def draw_qr(display, text, x, y, size_px):
    if qrcode is None:
        return
    code = qrcode.QRCode()
    code.set_text(text)
    w, h = code.get_size()
    cell = max(1, size_px // max(w, h))
    for cy in range(h):
        for cx in range(w):
            if code.get_module(cx, cy):
                display.rectangle(x + cx * cell, y + cy * cell, cell, cell)


def wrap(text, max_chars):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur = cur + " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_screens_common.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add screens/common.py tests/test_screens_common.py
git commit -m "feat(screens): shared drawing helpers (clear, rule, QR, wrap)"
```

---

## Task 5: Name-card screen

**Files:**
- Create: `screens/name_card.py`
- Test: `tests/test_screens_name_card.py`

- [ ] **Step 1: Write `tests/test_screens_name_card.py`**

```python
from types import SimpleNamespace

from tests.fakes.display import FakeDisplay

from screens.name_card import render


def _cfg():
    return SimpleNamespace(
        NAME="Philip Robb",
        TITLE="Technical Lead",
        ORG="Robb.Tech",
        URL="https://robb.tech",
    )


def test_renders_name_title_org():
    d = FakeDisplay()
    render(d, _cfg(), headshot_path="assets/headshot.bin")
    texts = d.texts()
    assert "Philip Robb" in texts
    assert "Technical Lead" in texts
    assert "Robb.Tech" in texts


def test_draws_headshot_image():
    d = FakeDisplay()
    render(d, _cfg(), headshot_path="assets/headshot.bin")
    image_calls = [args for name, args in d.calls if name == "image"]
    assert len(image_calls) == 1
    _, w, h, x, y = image_calls[0]
    assert (w, h) == (128, 128)
    assert x == 0 and y == 0


def test_draws_qr_for_url():
    d = FakeDisplay()
    render(d, _cfg(), headshot_path="assets/headshot.bin")
    rect_calls = [args for name, args in d.calls if name == "rectangle"]
    assert len(rect_calls) > 5


def test_calls_update():
    d = FakeDisplay()
    render(d, _cfg(), headshot_path="assets/headshot.bin")
    assert ("update", ()) in d.calls
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_screens_name_card.py -v`
Expected: failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `screens/name_card.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_screens_name_card.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add screens/name_card.py tests/test_screens_name_card.py
git commit -m "feat(screens): name-card screen with headshot and QR"
```

---

## Task 6: Contact screen

**Files:**
- Create: `screens/contact.py`
- Test: `tests/test_screens_contact.py`

- [ ] **Step 1: Write `tests/test_screens_contact.py`**

```python
from types import SimpleNamespace

from tests.fakes.display import FakeDisplay

from screens.contact import render


def test_renders_each_contact_field():
    d = FakeDisplay()
    cfg = SimpleNamespace(CONTACT={
        "email": "philip@teamrobb.com",
        "linkedin": "https://www.linkedin.com/in/philip-robb",
    })
    render(d, cfg)
    texts = " ".join(d.texts())
    assert "philip@teamrobb.com" in texts
    assert "linkedin" in texts.lower()


def test_draws_a_qr_per_field():
    d = FakeDisplay()
    cfg = SimpleNamespace(CONTACT={"a": "https://a.example", "b": "https://b.example"})
    render(d, cfg)
    rect_calls = [args for name, args in d.calls if name == "rectangle"]
    assert len(rect_calls) > 10  # at least a bunch of QR modules per code


def test_empty_contact_renders_without_error():
    d = FakeDisplay()
    render(d, SimpleNamespace(CONTACT={}))
    assert ("update", ()) in d.calls
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_screens_contact.py -v`
Expected: failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `screens/contact.py`**

```python
from screens.common import BLACK, HEIGHT, clear_white, draw_qr

_QR_SIZE = 40
_ROW_H = 44


def render(display, config):
    clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    items = list(config.CONTACT.items())[:3]  # 3 rows fit at 44 px each
    for idx, (label, value) in enumerate(items):
        y = idx * _ROW_H + 4
        display.text(label, 4, y, scale=1.0)
        display.text(value, 4, y + 16, scale=0.9)
        draw_qr(display, value, x=256, y=y, size_px=_QR_SIZE)

    display.update()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_screens_contact.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add screens/contact.py tests/test_screens_contact.py
git commit -m "feat(screens): contact screen with per-field QR codes"
```

---

## Task 7: Bio screen

**Files:**
- Create: `screens/bio.py`
- Test: `tests/test_screens_bio.py`

- [ ] **Step 1: Write `tests/test_screens_bio.py`**

```python
from types import SimpleNamespace

from tests.fakes.display import FakeDisplay

from screens.bio import render


def test_renders_bio_and_skills():
    d = FakeDisplay()
    cfg = SimpleNamespace(
        BIO="Technical lead building infrastructure and automation at Robb.Tech.",
        BIO_SKILLS="Python · Linux · networks · LLMs",
    )
    render(d, cfg)
    texts = " ".join(d.texts())
    assert "Technical lead" in texts
    assert "Python" in texts


def test_wraps_long_bio():
    d = FakeDisplay()
    cfg = SimpleNamespace(
        BIO="one two three four five six seven eight nine ten eleven twelve",
        BIO_SKILLS="x",
    )
    render(d, cfg)
    text_calls = [args for name, args in d.calls if name == "text"]
    # expect > 1 text call for the bio body (wrapped lines)
    assert len(text_calls) >= 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_screens_bio.py -v`
Expected: failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `screens/bio.py`**

```python
from screens.common import BLACK, clear_white, draw_header_rule, wrap

_LINE_H = 14
_WRAP_CHARS = 36


def render(display, config):
    clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    display.text("About", 4, 4, scale=1.2)
    draw_header_rule(display, y=22)

    y = 28
    for line in wrap(config.BIO, _WRAP_CHARS):
        display.text(line, 4, y, scale=1.0)
        y += _LINE_H

    y += 4
    display.text("Skills:", 4, y, scale=1.0)
    y += _LINE_H
    display.text(config.BIO_SKILLS, 4, y, scale=0.9)

    display.update()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_screens_bio.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add screens/bio.py tests/test_screens_bio.py
git commit -m "feat(screens): bio screen with wrapped body and skills line"
```

---

## Task 8: Now screen

**Files:**
- Create: `screens/now.py`
- Test: `tests/test_screens_now.py`

- [ ] **Step 1: Write `tests/test_screens_now.py`**

```python
from types import SimpleNamespace

from tests.fakes.display import FakeDisplay

from screens.now import render


def test_renders_now_text():
    d = FakeDisplay()
    render(d, SimpleNamespace(NOW="Building out the Robb.Tech platform."))
    texts = " ".join(d.texts())
    assert "Now" in texts
    assert "Robb.Tech" in texts


def test_wraps_long_now():
    d = FakeDisplay()
    cfg = SimpleNamespace(NOW="one two three four five six seven eight nine ten eleven twelve thirteen fourteen")
    render(d, cfg)
    text_calls = [args for name, args in d.calls if name == "text"]
    assert len(text_calls) >= 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_screens_now.py -v`
Expected: failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `screens/now.py`**

```python
from screens.common import BLACK, clear_white, draw_header_rule, wrap

_LINE_H = 16
_WRAP_CHARS = 28


def render(display, config):
    clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    display.text("Now", 4, 4, scale=1.4)
    draw_header_rule(display, y=24)

    y = 34
    for line in wrap(config.NOW, _WRAP_CHARS):
        display.text(line, 4, y, scale=1.2)
        y += _LINE_H

    display.update()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_screens_now.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add screens/now.py tests/test_screens_now.py
git commit -m "feat(screens): now screen with wrapped status text"
```

---

## Task 9: Logo screen

**Files:**
- Create: `screens/logo.py`
- Test: `tests/test_screens_logo.py`

- [ ] **Step 1: Write `tests/test_screens_logo.py`**

```python
from types import SimpleNamespace

from tests.fakes.display import FakeDisplay

from screens.logo import render


def test_draws_wordmark_full_bleed():
    d = FakeDisplay()
    render(d, SimpleNamespace(), wordmark_path="assets/robbtech_wordmark.bin")
    image_calls = [args for name, args in d.calls if name == "image"]
    assert len(image_calls) == 1
    _, w, h, x, y = image_calls[0]
    assert (w, h, x, y) == (296, 128, 0, 0)
    assert ("update", ()) in d.calls
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_screens_logo.py -v`
Expected: failure with `ModuleNotFoundError`.

- [ ] **Step 3: Write `screens/logo.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_screens_logo.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add screens/logo.py tests/test_screens_logo.py
git commit -m "feat(screens): logo screen full-bleed wordmark"
```

---

## Task 10: Badge mode controller

**Files:**
- Create: `modes/badge.py`
- Test: `tests/test_modes_badge.py`

- [ ] **Step 1: Write `tests/test_modes_badge.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_modes_badge.py -v`
Expected: failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `modes/badge.py`**

```python
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
```

`_SCREEN_NAMES` is a tuple of string names, not module objects. The `render_current` method looks each screen up in `globals()` so the test's `monkeypatch.setattr(badge, "name_card", ...)` is visible at call time — capturing module refs into a tuple at import time would bind the original modules and bypass the monkeypatch.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_modes_badge.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add modes/badge.py tests/test_modes_badge.py
git commit -m "feat(modes): badge mode screen deck controller"
```

---

## Task 11: Desk fetcher

**Files:**
- Create: `desk/fetcher.py`
- Test: `tests/test_desk_fetcher.py`

- [ ] **Step 1: Write `tests/test_desk_fetcher.py`**

```python
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from desk import fetcher


def _cfg():
    return SimpleNamespace(
        WIFI_SSID="net", WIFI_PSK="pw",
        AGGREGATOR_URL="http://h/badge.json",
        AGGREGATOR_TOKEN="tok",
    )


def test_connects_and_fetches(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.side_effect = [False, True]
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    response = MagicMock(status_code=200)
    response.json.return_value = {"weather": {"temp_f": 70}}
    monkeypatch.setattr(fetcher, "_http_get", lambda url, headers: response)

    data, marker = fetcher.fetch(_cfg(), last_data=None)

    wlan.active.assert_called_with(True)
    wlan.connect.assert_called_with("net", "pw")
    assert data == {"weather": {"temp_f": 70}}
    assert marker is None


def test_wifi_timeout_returns_last_with_offline(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = False
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    monkeypatch.setattr(fetcher, "_WIFI_TIMEOUT_S", 0.01)

    last = {"weather": {"temp_f": 69}}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert data == last
    assert marker == "offline"


def test_http_error_returns_last_with_offline(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)

    def boom(url, headers):
        raise OSError("conn reset")

    monkeypatch.setattr(fetcher, "_http_get", boom)
    last = {"weather": {"temp_f": 69}}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert data == last
    assert marker == "offline"


def test_non_200_returns_last_with_offline(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=500)
    monkeypatch.setattr(fetcher, "_http_get", lambda url, headers: response)

    last = {"weather": {"temp_f": 69}}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert data == last
    assert marker == "offline"


def test_bad_payload_returns_last_with_marker(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    response = MagicMock(status_code=200)
    response.json.side_effect = ValueError("bad json")
    monkeypatch.setattr(fetcher, "_http_get", lambda url, headers: response)

    last = {"weather": {"temp_f": 69}}
    data, marker = fetcher.fetch(_cfg(), last_data=last)

    assert data == last
    assert marker == "bad payload"


def test_stale_marker_when_no_previous_data(monkeypatch):
    wlan = MagicMock()
    wlan.isconnected.return_value = True
    monkeypatch.setattr(fetcher, "_make_wlan", lambda: wlan)
    monkeypatch.setattr(fetcher, "_http_get", lambda url, headers: (_ for _ in ()).throw(OSError("x")))

    data, marker = fetcher.fetch(_cfg(), last_data=None)
    assert data is None
    assert marker == "offline"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_desk_fetcher.py -v`
Expected: failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `desk/fetcher.py`**

```python
import time

try:
    import network
    import urequests
except ImportError:
    network = None
    urequests = None

_WIFI_TIMEOUT_S = 15.0


def _make_wlan():
    w = network.WLAN(network.STA_IF)
    return w


def _http_get(url, headers):
    return urequests.get(url, headers=headers, timeout=3)


def _connect_wifi(cfg):
    w = _make_wlan()
    w.active(True)
    if not w.isconnected():
        w.connect(cfg.WIFI_SSID, cfg.WIFI_PSK)
    deadline = time.time() + _WIFI_TIMEOUT_S
    while not w.isconnected():
        if time.time() > deadline:
            return False
        time.sleep(0.25)
    return True


def fetch(cfg, last_data):
    if not _connect_wifi(cfg):
        return last_data, "offline"

    try:
        r = _http_get(cfg.AGGREGATOR_URL, headers={"X-Badge-Token": cfg.AGGREGATOR_TOKEN})
        if r.status_code != 200:
            return last_data, "offline"
        try:
            return r.json(), None
        except (ValueError, Exception):
            return last_data, "bad payload"
    except Exception:
        return last_data, "offline"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_desk_fetcher.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add desk/fetcher.py tests/test_desk_fetcher.py
git commit -m "feat(desk): Wi-Fi connect + aggregator fetch with stale fallback"
```

---

## Task 12: Desk renderer

**Files:**
- Create: `desk/render.py`
- Test: `tests/test_desk_render.py`

- [ ] **Step 1: Write `tests/test_desk_render.py`**

```python
from tests.fakes.display import FakeDisplay

from desk.render import render


_PAYLOAD = {
    "generated_at": "2026-04-21T10:00:00-05:00",
    "weather": {"temp_f": 72, "summary": "sunny", "icon": "sun", "stale": False},
    "calendar": {"next": {"start": "2026-04-21T15:00:00-05:00", "title": "Standup"}, "stale": False},
    "desk": {"open_tickets": 4, "stale": False},
    "crm": {"tasks_due_today": 2, "stale": False},
}


def test_renders_four_tiles():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker=None)
    texts = " ".join(d.texts())
    assert "72" in texts
    assert "Standup" in texts
    assert "4" in texts
    assert "2" in texts


def test_draws_tile_grid_lines():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker=None)
    lines = [args for name, args in d.calls if name == "line"]
    # one horizontal and one vertical divider
    assert any(a[1] == a[3] for a in lines)  # horizontal
    assert any(a[0] == a[2] for a in lines)  # vertical


def test_stale_marker_rendered():
    d = FakeDisplay()
    render(d, _PAYLOAD, stale_marker="offline")
    texts = " ".join(d.texts())
    assert "offline" in texts


def test_no_calendar_shows_dash():
    d = FakeDisplay()
    payload = dict(_PAYLOAD, calendar={"next": None, "stale": False})
    render(d, payload, stale_marker=None)
    texts = " ".join(d.texts())
    assert "—" in texts or "no events" in texts.lower()


def test_renders_when_payload_none_with_marker():
    d = FakeDisplay()
    render(d, None, stale_marker="offline")
    texts = " ".join(d.texts())
    assert "offline" in texts
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_desk_render.py -v`
Expected: failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `desk/render.py`**

```python
from screens.common import BLACK, HEIGHT, WIDTH, clear_white


def _format_time(iso):
    # Expect "YYYY-MM-DDTHH:MM:SS±HH:MM" or date-only.
    if "T" not in iso:
        return iso
    t = iso.split("T", 1)[1]
    hhmm = t[:5]
    h = int(hhmm[:2])
    m = hhmm[3:5]
    ampm = "a" if h < 12 else "p"
    h12 = h % 12 or 12
    return f"{h12}:{m}{ampm}"


def _draw_weather(d, tile, x, y, w, h):
    if tile is None:
        d.text("weather: ?", x + 4, y + 4)
        return
    t = tile.get("temp_f")
    s = tile.get("summary", "")
    temp = f"{t}°F" if t is not None else "--°F"
    d.text(temp, x + 4, y + 4, scale=1.4)
    d.text(s, x + 4, y + 28, scale=1.0)
    if tile.get("stale"):
        d.text("(stale)", x + 4, y + 46, scale=0.8)


def _draw_calendar(d, tile, x, y, w, h):
    d.text("Next:", x + 4, y + 4, scale=1.0)
    if tile is None or tile.get("next") is None:
        d.text("— no events —", x + 4, y + 22, scale=1.0)
        return
    nxt = tile["next"]
    when = _format_time(nxt["start"])
    d.text(when, x + 4, y + 22, scale=1.2)
    title = nxt["title"]
    if len(title) > 18:
        title = title[:17] + "…"
    d.text(title, x + 4, y + 44, scale=1.0)
    if tile.get("stale"):
        d.text("(stale)", x + 4, y + 56, scale=0.8)


def _draw_desk(d, tile, x, y, w, h):
    n = tile.get("open_tickets") if tile else None
    label = f"{n}" if n is not None else "?"
    d.text(f"Desk: {label}", x + 4, y + 4, scale=1.2)
    d.text("tickets open", x + 4, y + 28, scale=0.9)
    if tile and tile.get("stale"):
        d.text("(stale)", x + 4, y + 46, scale=0.8)


def _draw_crm(d, tile, x, y, w, h):
    n = tile.get("tasks_due_today") if tile else None
    label = f"{n}" if n is not None else "?"
    d.text(f"CRM: {label}", x + 4, y + 4, scale=1.2)
    d.text("tasks today", x + 4, y + 28, scale=0.9)
    if tile and tile.get("stale"):
        d.text("(stale)", x + 4, y + 46, scale=0.8)


def render(display, payload, stale_marker):
    clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    mid_x = WIDTH // 2
    mid_y = HEIGHT // 2
    display.line(0, mid_y, WIDTH, mid_y)
    display.line(mid_x, 0, mid_x, HEIGHT)

    if payload is None:
        payload = {}
    _draw_weather(display, payload.get("weather"), 0, 0, mid_x, mid_y)
    _draw_calendar(display, payload.get("calendar"), mid_x, 0, WIDTH - mid_x, mid_y)
    _draw_desk(display, payload.get("desk"), 0, mid_y, mid_x, HEIGHT - mid_y)
    _draw_crm(display, payload.get("crm"), mid_x, mid_y, WIDTH - mid_x, HEIGHT - mid_y)

    if stale_marker:
        display.text(stale_marker, WIDTH - 64, HEIGHT - 10, scale=0.8)

    display.update()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_desk_render.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add desk/render.py tests/test_desk_render.py
git commit -m "feat(desk): 4-tile dashboard renderer with stale marker"
```

---

## Task 13: Desk mode controller

**Files:**
- Create: `modes/desk.py`
- Test: `tests/test_modes_desk.py`

- [ ] **Step 1: Write `tests/test_modes_desk.py`**

```python
from types import SimpleNamespace
from unittest.mock import MagicMock

from tests.fakes.display import FakeDisplay

import modes.desk as desk_mod


def _cfg():
    return SimpleNamespace(
        WIFI_SSID="n", WIFI_PSK="p",
        AGGREGATOR_URL="http://h/badge.json",
        AGGREGATOR_TOKEN="t",
        REFRESH_MINUTES=15,
    )


def test_refresh_cycle_persists_and_renders(monkeypatch):
    d = FakeDisplay()
    payload = {"weather": {"temp_f": 72, "summary": "sunny", "icon": "sun", "stale": False},
               "calendar": {"next": None, "stale": False},
               "desk": {"open_tickets": 0, "stale": False},
               "crm": {"tasks_due_today": 0, "stale": False}}

    monkeypatch.setattr(desk_mod, "fetch", lambda cfg, last: (payload, None))
    save_calls = []
    monkeypatch.setattr(desk_mod, "save_state", lambda p, s: save_calls.append((p, s)))
    load_calls = []
    monkeypatch.setattr(desk_mod, "load_state", lambda p: load_calls.append(p) or {"mode": "desk", "last_data": None})
    sleeps = []
    monkeypatch.setattr(desk_mod, "deepsleep_ms", lambda ms: sleeps.append(ms))

    controller = desk_mod.DeskMode(d, _cfg(), state_path="/state.json")
    controller.cycle()

    texts = " ".join(d.texts())
    assert "72" in texts
    assert save_calls, "state.save not called"
    assert save_calls[0][1]["last_data"] == payload
    assert sleeps == [15 * 60 * 1000]


def test_offline_uses_last_data(monkeypatch):
    d = FakeDisplay()
    last = {"weather": {"temp_f": 69, "summary": "cloud", "icon": "cloud", "stale": False},
            "calendar": {"next": None, "stale": False},
            "desk": {"open_tickets": 1, "stale": False},
            "crm": {"tasks_due_today": 0, "stale": False}}

    monkeypatch.setattr(desk_mod, "load_state", lambda p: {"mode": "desk", "last_data": last})
    monkeypatch.setattr(desk_mod, "fetch", lambda cfg, ld: (ld, "offline"))
    monkeypatch.setattr(desk_mod, "save_state", lambda p, s: None)
    monkeypatch.setattr(desk_mod, "deepsleep_ms", lambda ms: None)

    controller = desk_mod.DeskMode(d, _cfg(), state_path="/state.json")
    controller.cycle()

    texts = " ".join(d.texts())
    assert "69" in texts
    assert "offline" in texts


def test_button_a_forces_refresh(monkeypatch):
    d = FakeDisplay()
    fetches = []

    def fake_fetch(cfg, last):
        fetches.append(last)
        return ({"weather": None, "calendar": None, "desk": None, "crm": None}, "offline")

    monkeypatch.setattr(desk_mod, "load_state", lambda p: {"mode": "desk", "last_data": None})
    monkeypatch.setattr(desk_mod, "fetch", fake_fetch)
    monkeypatch.setattr(desk_mod, "save_state", lambda p, s: None)
    monkeypatch.setattr(desk_mod, "deepsleep_ms", lambda ms: None)

    controller = desk_mod.DeskMode(d, _cfg(), state_path="/state.json")
    controller.handle_button("A")
    assert len(fetches) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_modes_desk.py -v`
Expected: failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `modes/desk.py`**

```python
try:
    from machine import deepsleep as _deepsleep
except ImportError:
    def _deepsleep(ms):
        pass

from desk.fetcher import fetch
from desk.render import render
from state import load as load_state
from state import save as save_state


def deepsleep_ms(ms):
    _deepsleep(ms)


class DeskMode:
    def __init__(self, display, config, state_path="/state.json"):
        self.display = display
        self.config = config
        self.state_path = state_path

    def cycle(self):
        state = load_state(self.state_path)
        last = state.get("last_data")
        data, marker = fetch(self.config, last)
        render(self.display, data if data is not None else last, marker)
        if data is not None and marker is None:
            save_state(self.state_path, {"mode": "desk", "last_data": data})
        deepsleep_ms(self.config.REFRESH_MINUTES * 60 * 1000)

    def handle_button(self, btn):
        if btn == "A":
            self.cycle()
        elif btn == "UP":
            self.display.led(0)
        elif btn == "DOWN":
            self.display.halt()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_modes_desk.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add modes/desk.py tests/test_modes_desk.py
git commit -m "feat(modes): desk mode cycle — fetch, render, persist, sleep"
```

---

## Task 14: Long-press mode switch

**Files:**
- Create: `mode_switch.py`
- Test: `tests/test_mode_switch.py`

- [ ] **Step 1: Write `tests/test_mode_switch.py`**

```python
from tests.fakes.display import FakeDisplay

import mode_switch


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_long_press_detected_after_threshold():
    clock = Clock()
    d = FakeDisplay()
    d.press("B")
    detector = mode_switch.LongPressDetector(d, button="B", threshold_s=2.0, now=clock)

    clock.t = 0.0
    assert detector.poll() is False
    clock.t = 1.5
    assert detector.poll() is False
    clock.t = 2.5
    assert detector.poll() is True


def test_short_press_does_not_trigger():
    clock = Clock()
    d = FakeDisplay()
    detector = mode_switch.LongPressDetector(d, button="B", threshold_s=2.0, now=clock)

    d.press("B")
    clock.t = 0.5
    assert detector.poll() is False
    d.release("B")
    clock.t = 0.6
    assert detector.poll() is False


def test_detector_only_fires_once_per_press():
    clock = Clock()
    d = FakeDisplay()
    d.press("B")
    detector = mode_switch.LongPressDetector(d, button="B", threshold_s=2.0, now=clock)

    clock.t = 2.5
    assert detector.poll() is True
    clock.t = 3.0
    assert detector.poll() is False


def test_transition_flips_mode_and_persists(tmp_path):
    p = tmp_path / "state.json"
    p.write_text('{"mode": "badge", "last_data": null}')
    new = mode_switch.transition(str(p))
    assert new == "desk"
    import json
    assert json.loads(p.read_text())["mode"] == "desk"

    new = mode_switch.transition(str(p))
    assert new == "badge"


def test_transition_preserves_last_data(tmp_path):
    import json

    p = tmp_path / "state.json"
    p.write_text(json.dumps({"mode": "desk", "last_data": {"x": 1}}))
    mode_switch.transition(str(p))
    assert json.loads(p.read_text())["last_data"] == {"x": 1}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_mode_switch.py -v`
Expected: failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `mode_switch.py`**

```python
import time

from state import load, save


class LongPressDetector:
    def __init__(self, display, button, threshold_s=2.0, now=time.time):
        self.display = display
        self.button = button
        self.threshold = threshold_s
        self._now = now
        self._press_start = None
        self._fired = False

    def poll(self):
        pressed = self.display.pressed(self.button)
        t = self._now()
        if pressed:
            if self._press_start is None:
                self._press_start = t
                self._fired = False
            elif not self._fired and (t - self._press_start) >= self.threshold:
                self._fired = True
                return True
        else:
            self._press_start = None
            self._fired = False
        return False


def transition(state_path):
    state = load(state_path)
    current = state.get("mode", "badge")
    new = "desk" if current == "badge" else "badge"
    state["mode"] = new
    save(state_path, state)
    return new
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_mode_switch.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add mode_switch.py tests/test_mode_switch.py
git commit -m "feat: long-press detector and persisted mode transition"
```

---

## Task 15: `main.py` dispatcher

**Files:**
- Modify: `main.py`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write `tests/test_main.py`**

```python
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tests.fakes.display import FakeDisplay

import main


def _cfg_mod():
    return SimpleNamespace(
        NAME="P", TITLE="T", ORG="R", URL="u",
        CONTACT={}, BIO="b", BIO_SKILLS="s", NOW="n",
        WIFI_SSID="", WIFI_PSK="",
        AGGREGATOR_URL="", AGGREGATOR_TOKEN="", REFRESH_MINUTES=15,
    )


def test_dispatches_to_badge_mode(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    p.write_text('{"mode": "badge", "last_data": null}')

    badge_inst = MagicMock()
    desk_inst = MagicMock()
    monkeypatch.setattr(main, "_build_display", lambda: FakeDisplay())
    monkeypatch.setattr(main, "_load_config", _cfg_mod)
    monkeypatch.setattr(main, "BadgeMode", lambda d, c: badge_inst)
    monkeypatch.setattr(main, "DeskMode", lambda d, c, state_path: desk_inst)

    main.run(state_path=str(p))

    badge_inst.render_current.assert_called_once()
    desk_inst.cycle.assert_not_called()


def test_dispatches_to_desk_mode(tmp_path, monkeypatch):
    p = tmp_path / "state.json"
    p.write_text('{"mode": "desk", "last_data": null}')

    badge_inst = MagicMock()
    desk_inst = MagicMock()
    monkeypatch.setattr(main, "_build_display", lambda: FakeDisplay())
    monkeypatch.setattr(main, "_load_config", _cfg_mod)
    monkeypatch.setattr(main, "BadgeMode", lambda d, c: badge_inst)
    monkeypatch.setattr(main, "DeskMode", lambda d, c, state_path: desk_inst)

    main.run(state_path=str(p))

    desk_inst.cycle.assert_called_once()
    badge_inst.render_current.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_main.py -v`
Expected: failures (main module has no `run` / referenced attributes).

- [ ] **Step 3: Overwrite `main.py`**

```python
try:
    import badger2040w
except ImportError:
    badger2040w = None

from modes.badge import BadgeMode
from modes.desk import DeskMode
from state import load as load_state


def _build_display():
    return badger2040w.Badger2040W()


def _load_config():
    import config
    return config


def run(state_path="/state.json"):
    state = load_state(state_path)
    mode = state.get("mode", "badge")
    display = _build_display()
    config = _load_config()

    if mode == "desk":
        DeskMode(display, config, state_path=state_path).cycle()
    else:
        BadgeMode(display, config).render_current()


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_main.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: main.py dispatches to badge or desk mode from state.json"
```

---

## Task 16: Dither tool

**Files:**
- Create: `tools/dither_image.py`
- Test: `tests/test_tools_dither.py`

- [ ] **Step 1: Write `tests/test_tools_dither.py`**

```python
from pathlib import Path

import pytest
from PIL import Image

from tools.dither_image import convert


def _make_image(tmp_path: Path, w: int, h: int) -> Path:
    img = Image.new("RGB", (w, h), color="white")
    for y in range(h):
        for x in range(w):
            v = int(255 * (x / w))
            img.putpixel((x, y), (v, v, v))
    p = tmp_path / "src.png"
    img.save(p)
    return p


def test_output_byte_count_matches_packed_size(tmp_path):
    src = _make_image(tmp_path, 128, 128)
    out = tmp_path / "out.bin"
    convert(str(src), str(out), width=128, height=128)
    assert out.stat().st_size == 128 * 128 // 8


def test_output_is_packed_msb_first(tmp_path):
    # All-black input should produce all 0x00.
    black = Image.new("L", (32, 8), color=0)
    src = tmp_path / "black.png"
    black.save(src)
    out = tmp_path / "out.bin"
    convert(str(src), str(out), width=32, height=8)
    data = out.read_bytes()
    assert data == b"\x00" * 32  # 32*8 pixels / 8 = 32 bytes


def test_all_white_produces_all_ones(tmp_path):
    white = Image.new("L", (32, 8), color=255)
    src = tmp_path / "white.png"
    white.save(src)
    out = tmp_path / "out.bin"
    convert(str(src), str(out), width=32, height=8)
    data = out.read_bytes()
    assert data == b"\xff" * 32


def test_resize_to_target_dims(tmp_path):
    src = _make_image(tmp_path, 600, 600)
    out = tmp_path / "out.bin"
    convert(str(src), str(out), width=128, height=128)
    assert out.stat().st_size == 128 * 128 // 8


def test_cli_entrypoint(tmp_path, monkeypatch):
    src = _make_image(tmp_path, 64, 64)
    out = tmp_path / "cli.bin"

    from tools import dither_image
    dither_image.main(["--in", str(src), "--out", str(out), "--width", "64", "--height", "64"])

    assert out.stat().st_size == 64 * 64 // 8
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest tests/test_tools_dither.py -v`
Expected: 5 failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `tools/dither_image.py`**

```python
import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def _pack_bits(bits: np.ndarray) -> bytes:
    # bits shape (H, W) with values 0 or 1, W must be multiple of 8.
    h, w = bits.shape
    if w % 8 != 0:
        raise ValueError("width must be a multiple of 8")
    out = bytearray()
    for y in range(h):
        row = bits[y]
        for x in range(0, w, 8):
            byte = 0
            for b in range(8):
                byte = (byte << 1) | int(row[x + b])
            out.append(byte)
    return bytes(out)


def convert(src_path: str, out_path: str, width: int, height: int) -> None:
    img = Image.open(src_path).convert("L")
    img = img.resize((width, height), Image.LANCZOS)
    img = img.convert("1", dither=Image.FLOYDSTEINBERG)
    arr = np.array(img, dtype=np.uint8)  # 0 or 255
    bits = (arr > 0).astype(np.uint8)
    data = _pack_bits(bits)
    Path(out_path).write_bytes(data)


def main(argv=None):
    p = argparse.ArgumentParser(description="1-bit dither for Badger 2040 W")
    p.add_argument("--in", dest="src", required=True)
    p.add_argument("--out", dest="out", required=True)
    p.add_argument("--width", type=int, required=True)
    p.add_argument("--height", type=int, required=True)
    args = p.parse_args(argv)
    convert(args.src, args.out, args.width, args.height)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest tests/test_tools_dither.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/dither_image.py tests/test_tools_dither.py
git commit -m "feat(tools): dither_image.py — 1-bit packed .bin output"
```

---

## Task 17: Placeholder assets

**Files:**
- Create: `tools/make_placeholder_assets.py`
- Create: `assets/headshot.bin`
- Create: `assets/robbtech_wordmark.bin`

- [ ] **Step 1: Write `tools/make_placeholder_assets.py`**

```python
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.dither_image import convert


def _headshot(tmp: Path) -> Path:
    img = Image.new("L", (128, 128), color=255)
    draw = ImageDraw.Draw(img)
    draw.ellipse((44, 20, 84, 60), fill=60)          # head
    draw.pieslice((24, 60, 104, 140), 180, 360, fill=60)  # shoulders
    p = tmp / "headshot.png"
    img.save(p)
    return p


def _wordmark(tmp: Path) -> Path:
    img = Image.new("L", (296, 128), color=255)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
    except OSError:
        font = ImageFont.load_default()
    text = "ROBB.TECH"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((296 - tw) // 2 - bbox[0], (128 - th) // 2 - bbox[1]), text, fill=0, font=font)
    p = tmp / "wordmark.png"
    img.save(p)
    return p


def main():
    import tempfile

    assets = Path(__file__).resolve().parent.parent / "assets"
    assets.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        convert(str(_headshot(tmp)), str(assets / "headshot.bin"), 128, 128)
        convert(str(_wordmark(tmp)), str(assets / "robbtech_wordmark.bin"), 296, 128)
    print(f"Wrote {assets}/headshot.bin and {assets}/robbtech_wordmark.bin")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate the placeholder bins**

Run:
```bash
cd ~/code/badger
source .venv/bin/activate
python -m tools.make_placeholder_assets
```
Expected: `Wrote .../assets/headshot.bin and .../assets/robbtech_wordmark.bin`.

- [ ] **Step 3: Verify sizes**

Run:
```bash
stat -c '%n %s' ~/code/badger/assets/headshot.bin ~/code/badger/assets/robbtech_wordmark.bin
```
Expected: `headshot.bin 2048` (128·128/8) and `robbtech_wordmark.bin 4736` (296·128/8).

- [ ] **Step 4: Commit**

```bash
git add tools/make_placeholder_assets.py assets/headshot.bin assets/robbtech_wordmark.bin
git commit -m "feat(assets): placeholder headshot and wordmark bins + generator"
```

When a real headshot PNG is provided, rerun:
```
python -m tools.dither_image --in /path/to/headshot.png --out assets/headshot.bin --width 128 --height 128
```

---

## Task 18: `tools/flash.sh`

**Files:**
- Create: `tools/flash.sh`

- [ ] **Step 1: Write `tools/flash.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

DEVICE="${DEVICE:-/dev/ttyACM0}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MP="mpremote connect $DEVICE"

echo "Flashing to $DEVICE from $HERE"

$MP mkdir :modes || true
$MP mkdir :screens || true
$MP mkdir :desk || true
$MP mkdir :assets || true

$MP cp "$HERE/main.py" :main.py
$MP cp "$HERE/state.py" :state.py
$MP cp "$HERE/mode_switch.py" :mode_switch.py

for f in "$HERE/modes"/*.py; do $MP cp "$f" ":modes/$(basename "$f")"; done
for f in "$HERE/screens"/*.py; do $MP cp "$f" ":screens/$(basename "$f")"; done
for f in "$HERE/desk"/*.py; do $MP cp "$f" ":desk/$(basename "$f")"; done
for f in "$HERE/assets"/*.bin; do $MP cp "$f" ":assets/$(basename "$f")"; done

if [ ! -f "$HERE/config.py" ]; then
  echo "!! $HERE/config.py missing — copy config.example.py and fill in secrets before flashing config."
else
  $MP cp "$HERE/config.py" :config.py
fi

if [ ! -f "$HERE/state.json" ] || [ "$(cat "$HERE/state.json")" = "{}" ]; then
  $MP exec 'open("/state.json","w").write("{}")'
else
  $MP cp "$HERE/state.json" :state.json
fi

echo "Done. Soft-reset:"
$MP soft-reset
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x ~/code/badger/tools/flash.sh && bash -n ~/code/badger/tools/flash.sh`
Expected: no output (script parses cleanly).

- [ ] **Step 3: Commit**

```bash
git add tools/flash.sh
git commit -m "chore(tools): flash.sh mpremote wrapper for firmware + assets"
```

---

## Task 19: On-device smoke test (manual)

No files change. This task verifies the firmware on real hardware.

- [ ] **Step 1: Confirm device is reachable without sudo**

Run: `mpremote devs`
Expected: one line matching `/dev/ttyACM0 ... MicroPython Board in FS mode`.

- [ ] **Step 2: Create a real `config.py` from the template**

Run:
```bash
cp ~/code/badger/config.example.py ~/code/badger/config.py
$EDITOR ~/code/badger/config.py    # fill in WIFI_*, AGGREGATOR_TOKEN
```

Do **not** commit `config.py` (already excluded via `.gitignore` — if not, add it before continuing).

- [ ] **Step 3: Flash the device**

Run: `~/code/badger/tools/flash.sh`
Expected: each `cp :modes/badge.py ...` line completes without error; ends with `Done. Soft-reset:`.

- [ ] **Step 4: Watch the serial console during boot**

Run: `mpremote connect /dev/ttyACM0 repl`
Press Ctrl-D to soft-reboot inside the REPL. Expected: no tracebacks. Ctrl-] to exit REPL.

- [ ] **Step 5: Badge-mode navigation**

The device should be in badge mode (default state). Verify each transition by watching the display:
- Press C five times → cycles through all 5 screens, wrapping to screen 1.
- Press A → goes back one screen.
- Press B → redraws current screen.
- Press UP → on-board LED toggles.
- Press DOWN → display goes to halt; any subsequent button wakes it.

- [ ] **Step 6: Mode toggle**

Hold B for ≥ 2 s. Expected: screen redraws with a "switching to desk…" message, device soft-resets, comes back in desk mode with the aggregator dashboard (or with the "offline" marker if aggregator unreachable).

- [ ] **Step 7: Desk mode fetch**

With the aggregator service running on endevour (`systemctl --user status badger` reports `active`), press A on the badge. Expected: full refresh with current tile values. Confirm the values match `curl -s -H "X-Badge-Token: <token>" http://endevour.robb.tech:8088/badge.json`.

- [ ] **Step 8: Offline path**

Stop the aggregator (`systemctl --user stop badger`). Press A on the badge. Expected: dashboard stays rendered with the previous values and an "offline" marker. Restart the aggregator.

- [ ] **Step 9: Bad-payload path**

Temporarily return a non-JSON body from the aggregator (e.g., route `/badge.json` to a `return "nope"` in a scratch test branch, or use `socat` to intercept and rewrite). Press A. Expected: "bad payload" marker. Revert the aggregator change.

- [ ] **Step 10: Battery overnight**

Unplug USB. Long-press B to return to badge mode. Leave on 400 mAh LiPo overnight. Expected: still responds to A/C the next morning. This verifies `halt()` drops current as designed. No commit; log result in the repo's running notes if desired.

---

## Self-Review

**Spec coverage:**
- Dual-mode firmware with state-persisted mode toggle → Tasks 1, 3, 14, 15.
- 5 badge screens with specified content and button bindings → Tasks 4–9, 10.
- `halt()` after render in badge mode, UP=LED, DOWN=halt → Task 10.
- Desk mode: Wi-Fi on boot, 15-min deepsleep, 4 tiles, failure markers → Tasks 11, 12, 13.
- Button A = force refresh, B-long = toggle mode, UP/DOWN bindings in desk mode → Tasks 13, 14.
- Mode switch: ≥ 2 s B long-press, write state.json, soft-reset → Tasks 14, 15, 19 Step 6.
- Dither tool with pytest round-trip → Task 16.
- Flash wrapper (`mpremote`/`picotool`) → Task 18. (Plan uses `mpremote` only; `picotool` is for UF2 flashing which is not required because factory firmware is already present per the memory-system state-of-hardware note.)
- Config template → Task 1 (`config.example.py`).
- On-device smoke tests: flash, mode-toggle persistence, Wi-Fi-off fallback, overnight battery → Task 19 Steps 3, 6, 8, 10.
- Host-side test for dither tool → Task 16.
- Host stubs avoid coupling tests to device-only libraries → Task 2.

**Placeholder scan:** none — every step has complete code or a complete command. The placeholder *assets* generated in Task 17 are an explicit design decision (headshot source PNG not yet available, per spec Open Questions); the firmware works on-device from day one, and rerunning the dither tool when a real image arrives is a one-liner.

**Type consistency:**
- Tile keys (`weather.temp_f/summary/icon/stale`, `calendar.next.{start,title}/stale`, `desk.open_tickets/stale`, `crm.tasks_due_today/stale`) match the aggregator plan's schemas verbatim — same names used by `desk/render.py` and its tests (Task 12) and by `modes/desk.py` (Task 13).
- `BadgeMode.handle_button` / `DeskMode.handle_button` take a string button identifier; the set `{"A","B","C","UP","DOWN"}` is consistent with `tests/stubs/badger2040w.py` and the `FakeDisplay`.
- `state` dict shape `{"mode": "badge"|"desk", "last_data": ...}` is produced in Task 3 and consumed unchanged by Tasks 13, 14, 15.

**Assumptions carried forward:**
- Pimoroni badger2040w firmware API (`Badger2040W`, button constants, `.halt()`, `.image(buf, w, h, x, y)`, `.set_font("bitmap8"|"bitmap14_outline")`) matches the current stable release on-device. If the in-REPL smoke test (Task 19 Step 4) reveals a rename, patch the stub in `tests/stubs/badger2040w.py` plus the single `main.py` call site.
- `jpegdec` import in the stub is present for future use (e.g., if a .jpg version of the headshot ships later); no current module imports it. Leaving the stub in place avoids a refactor when that happens.
- Desk mode uses `machine.deepsleep`; waking via button requires USB power (spec's assumption). If battery desk mode is ever required, revisit.
