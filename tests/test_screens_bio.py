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
    assert len(text_calls) >= 3