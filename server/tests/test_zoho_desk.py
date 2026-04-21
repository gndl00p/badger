import json

import httpx
import pytest
import respx

from server.config import Settings
from server.upstreams import zoho_desk as desk


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("BADGE_TOKEN", "t")
    monkeypatch.setenv("WEATHER_LATITUDE", "0")
    monkeypatch.setenv("WEATHER_LONGITUDE", "0")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/tmp/x")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "x@example.com")
    monkeypatch.setenv("ZOHODESK_CLIENT_ID", "dcid")
    monkeypatch.setenv("ZOHODESK_CLIENT_SECRET", "dcs")
    monkeypatch.setenv("ZOHODESK_REFRESH_TOKEN", "drt")
    monkeypatch.setenv("ZOHODESK_ORG_ID", "42")
    monkeypatch.setenv("ZOHOCRM_CLIENT_ID", "a")
    monkeypatch.setenv("ZOHOCRM_CLIENT_SECRET", "b")
    monkeypatch.setenv("ZOHOCRM_REFRESH_TOKEN", "c")
    monkeypatch.setenv("ZOHOCRM_USER_ID", "99")
    return Settings()


@pytest.fixture(autouse=True)
def reset_state():
    desk._cache.__init__(ttl_seconds=desk._cache.ttl)
    desk._token_cache.__init__(ttl_seconds=desk._token_cache.ttl)


@pytest.mark.asyncio
async def test_desk_happy_path(settings, fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())
    count = json.loads((fixtures_dir / "zoho_desk_count.json").read_text())

    with respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        count_route = m.get("https://desk.zoho.com/api/v1/ticketsCount").mock(
            return_value=httpx.Response(200, json=count)
        )

        async with httpx.AsyncClient() as client:
            result = await desk.get(client, settings)

    assert result == {"open_tickets": 4, "stale": False}
    req = count_route.calls[0].request
    assert req.headers["Authorization"] == "Zoho-oauthtoken test-access-token"
    assert req.headers["orgId"] == "42"
    assert req.url.params["statusType"] == "Open"


@pytest.mark.asyncio
async def test_desk_reuses_access_token(settings, fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())
    count = json.loads((fixtures_dir / "zoho_desk_count.json").read_text())

    with respx.mock() as m:
        tok_route = m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        m.get("https://desk.zoho.com/api/v1/ticketsCount").mock(
            return_value=httpx.Response(200, json=count)
        )

        async with httpx.AsyncClient() as client:
            await desk.get(client, settings)

        # Expire the data cache so we re-fetch, but the token cache is still fresh.
        desk._cache._entry = None

        async with httpx.AsyncClient() as client:
            await desk.get(client, settings)

    assert tok_route.call_count == 1


@pytest.mark.asyncio
async def test_desk_stale_fallback(settings, fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())
    count = json.loads((fixtures_dir / "zoho_desk_count.json").read_text())

    with respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        m.get("https://desk.zoho.com/api/v1/ticketsCount").mock(
            return_value=httpx.Response(200, json=count)
        )
        async with httpx.AsyncClient() as client:
            await desk.get(client, settings)

    desk._cache._entry = (desk._cache._entry[0] - 1e6, desk._cache._entry[1])

    # Token cache still fresh (3000 s TTL) — cached token is reused, so the
    # stale path is triggered by the tickets endpoint failing instead.
    with respx.mock() as m:
        m.get("https://desk.zoho.com/api/v1/ticketsCount").mock(
            return_value=httpx.Response(500)
        )
        async with httpx.AsyncClient() as client:
            result = await desk.get(client, settings)

    assert result == {"open_tickets": 4, "stale": True}


@pytest.mark.asyncio
async def test_desk_default_when_never_succeeded(settings):
    with respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(500)
        )
        async with httpx.AsyncClient() as client:
            result = await desk.get(client, settings)

    assert result == {"open_tickets": 0, "stale": True}