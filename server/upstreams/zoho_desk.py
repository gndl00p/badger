import httpx

from server.cache import TTLCache
from server.config import Settings

_cache = TTLCache(ttl_seconds=30)
_token_cache = TTLCache(ttl_seconds=3000)  # refresh inside the 3600s typical lifetime


async def _get_access_token(client: httpx.AsyncClient, settings: Settings) -> str:
    tok = _token_cache.get_fresh()
    if tok is not None:
        return tok
    r = await client.post(
        f"{settings.zoho_accounts_host}/oauth/v2/token",
        params={
            "refresh_token": settings.zohodesk_refresh_token,
            "client_id": settings.zohodesk_client_id,
            "client_secret": settings.zohodesk_client_secret,
            "grant_type": "refresh_token",
        },
        timeout=2.0,
    )
    r.raise_for_status()
    access = r.json()["access_token"]
    _token_cache.set(access)
    return access


async def _fetch(client: httpx.AsyncClient, settings: Settings) -> dict:
    access = await _get_access_token(client, settings)
    r = await client.get(
        f"{settings.zohodesk_api_host}/api/v1/ticketsCount",
        params={"statusType": "Open"},
        headers={
            "Authorization": f"Zoho-oauthtoken {access}",
            "orgId": settings.zohodesk_org_id,
        },
        timeout=2.0,
    )
    r.raise_for_status()
    return {"open_tickets": int(r.json()["count"]), "stale": False}


async def get(client: httpx.AsyncClient, settings: Settings) -> dict:
    fresh = _cache.get_fresh()
    if fresh is not None:
        return fresh
    try:
        data = await _fetch(client, settings)
        _cache.set(data)
        return data
    except Exception:
        stale = _cache.get_any()
        if stale is None:
            return {"open_tickets": 0, "stale": True}
        return {**stale, "stale": True}