from datetime import date

import httpx

from server.cache import TTLCache
from server.config import Settings

_cache = TTLCache(ttl_seconds=30)
_token_cache = TTLCache(ttl_seconds=3000)


async def _get_access_token(client: httpx.AsyncClient, settings: Settings) -> str:
    tok = _token_cache.get_fresh()
    if tok is not None:
        return tok
    r = await client.post(
        f"{settings.zoho_accounts_host}/oauth/v2/token",
        params={
            "refresh_token": settings.zohocrm_refresh_token,
            "client_id": settings.zohocrm_client_id,
            "client_secret": settings.zohocrm_client_secret,
            "grant_type": "refresh_token",
        },
        timeout=2.0,
    )
    r.raise_for_status()
    access = r.json()["access_token"]
    _token_cache.set(access)
    return access


def _build_query(user_id: str, today: date) -> str:
    return (
        "select id from Tasks "
        f"where Due_Date = '{today.isoformat()}' "
        f"and Status != 'Completed' "
        f"and Owner.id = '{user_id}' "
        "limit 200"
    )


async def _fetch(client: httpx.AsyncClient, settings: Settings) -> dict:
    access = await _get_access_token(client, settings)
    query = _build_query(settings.zohocrm_user_id, date.today())
    r = await client.post(
        f"{settings.zohocrm_api_host}/crm/v8/coql",
        headers={"Authorization": f"Zoho-oauthtoken {access}"},
        json={"select_query": query},
        timeout=2.0,
    )
    if r.status_code == 204:
        return {"tasks_due_today": 0, "stale": False}
    r.raise_for_status()
    payload = r.json()
    count = payload.get("info", {}).get("count")
    if count is None:
        count = len(payload.get("data", []))
    return {"tasks_due_today": int(count), "stale": False}


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
            return {"tasks_due_today": 0, "stale": True}
        return {**stale, "stale": True}