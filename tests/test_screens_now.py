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