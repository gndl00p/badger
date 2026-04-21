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