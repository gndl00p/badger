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