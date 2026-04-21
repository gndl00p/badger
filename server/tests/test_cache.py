import time

from server.cache import TTLCache


def test_cache_empty_returns_none():
    c = TTLCache(ttl_seconds=60)
    assert c.get_fresh() is None
    assert c.get_any() is None


def test_cache_fresh_within_ttl(monkeypatch):
    c = TTLCache(ttl_seconds=60)
    t = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: t[0])

    c.set({"x": 1})
    t[0] += 30
    assert c.get_fresh() == {"x": 1}


def test_cache_stale_past_ttl(monkeypatch):
    c = TTLCache(ttl_seconds=60)
    t = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: t[0])

    c.set({"x": 1})
    t[0] += 120
    assert c.get_fresh() is None
    assert c.get_any() == {"x": 1}


def test_cache_overwrite(monkeypatch):
    c = TTLCache(ttl_seconds=60)
    t = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: t[0])

    c.set({"x": 1})
    t[0] += 5
    c.set({"x": 2})
    assert c.get_fresh() == {"x": 2}