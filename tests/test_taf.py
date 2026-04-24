from tests.fakes.display import FakeDisplay

import taf


def test_renders_taf_title_and_station():
    d = FakeDisplay()
    taf.render(d, "TAF KLBB 242330Z 2500/2524 21012KT P6SM SCT060",
               station="KLBB")
    texts = " ".join(d.texts())
    assert "TAF" in texts
    assert "KLBB" in texts


def test_renders_back_hint():
    d = FakeDisplay()
    taf.render(d, "TAF KLBB 242330Z 2500/2524 21012KT")
    texts = " ".join(d.texts())
    assert "B back" in texts


def test_missing_taf_placeholder():
    d = FakeDisplay()
    taf.render(d, None)
    texts = " ".join(d.texts())
    assert "no TAF" in texts


def test_wraps_long_taf():
    d = FakeDisplay()
    long_taf = "TAF KLBB 242330Z 2500/2524 " + " ".join(["SOMEVERYLONGWORDXYZ"] * 30)
    taf.render(d, long_taf)
    texts = [args[0] for name, args in d.calls if name == "text"]
    assert len(texts) >= 6


def test_overflow_hint_when_oversized():
    d = FakeDisplay()
    long_taf = " ".join(["XXX{0}".format(i) for i in range(200)])
    taf.render(d, long_taf)
    texts = " ".join(d.texts())
    assert "more" in texts
