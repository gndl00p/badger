import json

import httpx
import pytest
import respx
from freezegun import freeze_time

from server.config import Settings
from server.upstreams import zoho_crm as crm


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
    monkeypatch.setenv("ZOHOCRM_CLIENT_ID", "ccid")
    monkeypatch.setenv("ZOHOCRM_CLIENT_SECRET", "ccs")
    monkeypatch.setenv("ZOHOCRM_REFRESH_TOKEN", "crt")
    monkeypatch.setenv("ZOHOCRM_USER_ID", "99")
    return Settings()


@pytest.fixture(autouse=True)
def reset_state():
    crm._cache.__init__(ttl_seconds=crm._cache.ttl)
    crm._token_cache.__init__(ttl_seconds=crm._token_cache.ttl)


@pytest.mark.asyncio
@freeze_time("2026-04-21T10:00:00-05:00")
async def test_crm_happy_path(settings, fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())
    coql = json.loads((fixtures_dir / "zoho_crm_coql.json").read_text())

    with respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        coql_route = m.post("https://www.zohoapis.com/crm/v8/coql").mock(
            return_value=httpx.Response(200, json=coql)
        )

        async with httpx.AsyncClient() as client:
            result = await crm.get(client, settings)

    assert result == {"tasks_due_today": 2, "stale": False}
    body = json.loads(coql_route.calls[0].request.content.decode())
    assert "Due_Date = '2026-04-21'" in body["select_query"]
    assert "Owner.id = '99'" in body["select_query"]
    assert "Status != 'Completed'" in body["select_query"]
    assert coql_route.calls[0].request.headers["Authorization"] == "Zoho-oauthtoken test-access-token"


@pytest.mark.asyncio
@freeze_time("2026-04-21T10:00:00-05:00")
async def test_crm_empty_results(settings, fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())

    with respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        m.post("https://www.zohoapis.com/crm/v8/coql").mock(
            return_value=httpx.Response(204)
        )

        async with httpx.AsyncClient() as client:
            result = await crm.get(client, settings)

    assert result == {"tasks_due_today": 0, "stale": False}


@pytest.mark.asyncio
@freeze_time("2026-04-21T10:00:00-05:00")
async def test_crm_stale_fallback(settings, fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())
    coql = json.loads((fixtures_dir / "zoho_crm_coql.json").read_text())

    with respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        m.post("https://www.zohoapis.com/crm/v8/coql").mock(
            return_value=httpx.Response(200, json=coql)
        )
        async with httpx.AsyncClient() as client:
            await crm.get(client, settings)

    crm._cache._entry = (crm._cache._entry[0] - 1e6, crm._cache._entry[1])

    # Token cache still fresh (3000 s TTL) — cached token is reused, so the
    # stale path is triggered by the COQL endpoint failing instead.
    with respx.mock() as m:
        m.post("https://www.zohoapis.com/crm/v8/coql").mock(
            return_value=httpx.Response(500)
        )
        async with httpx.AsyncClient() as client:
            result = await crm.get(client, settings)

    assert result == {"tasks_due_today": 2, "stale": True}


@pytest.mark.asyncio
async def test_crm_default_when_never_succeeded(settings):
    with respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(500)
        )
        async with httpx.AsyncClient() as client:
            result = await crm.get(client, settings)

    assert result == {"tasks_due_today": 0, "stale": True}