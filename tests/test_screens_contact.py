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
    assert len(rect_calls) > 10


def test_empty_contact_renders_without_error():
    d = FakeDisplay()
    render(d, SimpleNamespace(CONTACT={}))
    assert ("update", ()) in d.calls