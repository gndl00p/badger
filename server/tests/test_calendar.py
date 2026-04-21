from unittest.mock import MagicMock, patch

import pytest

from server.config import Settings
from server.upstreams import calendar as cal


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("BADGE_TOKEN", "t")
    monkeypatch.setenv("WEATHER_LATITUDE", "0")
    monkeypatch.setenv("WEATHER_LONGITUDE", "0")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/tmp/x")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "x@example.com")
    monkeypatch.setenv("ZOHODESK_CLIENT_ID", "a")
    monkeypatch.setenv("ZOHODESK_CLIENT_SECRET", "b")
    monkeypatch.setenv("ZOHODESK_REFRESH_TOKEN", "c")
    monkeypatch.setenv("ZOHODESK_ORG_ID", "1")
    monkeypatch.setenv("ZOHOCRM_CLIENT_ID", "a")
    monkeypatch.setenv("ZOHOCRM_CLIENT_SECRET", "b")
    monkeypatch.setenv("ZOHOCRM_REFRESH_TOKEN", "c")
    monkeypatch.setenv("ZOHOCRM_USER_ID", "99")
    return Settings()


@pytest.fixture(autouse=True)
def reset_cache():
    cal._cache.__init__(ttl_seconds=cal._cache.ttl)


def _fake_service(items):
    service = MagicMock()
    service.events.return_value.list.return_value.execute.return_value = {"items": items}
    return service


@pytest.mark.asyncio
async def test_calendar_happy_path(settings):
    items = [{"start": {"dateTime": "2026-04-21T15:00:00-05:00"}, "summary": "Standup"}]
    with patch.object(cal, "_build_service", return_value=_fake_service(items)):
        result = await cal.get(settings)

    assert result["stale"] is False
    assert result["next"] == {"start": "2026-04-21T15:00:00-05:00", "title": "Standup"}


@pytest.mark.asyncio
async def test_calendar_no_events(settings):
    with patch.object(cal, "_build_service", return_value=_fake_service([])):
        result = await cal.get(settings)

    assert result == {"next": None, "stale": False}


@pytest.mark.asyncio
async def test_calendar_all_day_event(settings):
    items = [{"start": {"date": "2026-04-22"}, "summary": "Company holiday"}]
    with patch.object(cal, "_build_service", return_value=_fake_service(items)):
        result = await cal.get(settings)

    assert result["next"] == {"start": "2026-04-22", "title": "Company holiday"}


@pytest.mark.asyncio
async def test_calendar_stale_fallback(settings):
    items = [{"start": {"dateTime": "2026-04-21T15:00:00-05:00"}, "summary": "Standup"}]
    with patch.object(cal, "_build_service", return_value=_fake_service(items)):
        await cal.get(settings)

    cal._cache._entry = (cal._cache._entry[0] - 1e6, cal._cache._entry[1])

    with patch.object(cal, "_build_service", side_effect=RuntimeError("boom")):
        result = await cal.get(settings)

    assert result["stale"] is True
    assert result["next"]["title"] == "Standup"


@pytest.mark.asyncio
async def test_calendar_default_when_never_succeeded(settings):
    with patch.object(cal, "_build_service", side_effect=RuntimeError("boom")):
        result = await cal.get(settings)

    assert result == {"next": None, "stale": True}