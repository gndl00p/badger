import asyncio
from datetime import datetime, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build

from server.cache import TTLCache
from server.config import Settings

_cache = TTLCache(ttl_seconds=60)
_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _build_service(settings: Settings):
    creds = service_account.Credentials.from_service_account_file(
        settings.google_service_account_json, scopes=_SCOPES
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _extract_next(items: list) -> dict | None:
    if not items:
        return None
    ev = items[0]
    start = ev.get("start", {})
    when = start.get("dateTime") or start.get("date")
    if not when:
        return None
    return {"start": when, "title": ev.get("summary", "(no title)")}


def _fetch_sync(settings: Settings) -> dict:
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=24)
    service = _build_service(settings)
    result = (
        service.events()
        .list(
            calendarId=settings.google_calendar_id,
            timeMin=now.isoformat(),
            timeMax=window_end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=1,
        )
        .execute()
    )
    return {"next": _extract_next(result.get("items", [])), "stale": False}


async def get(settings: Settings) -> dict:
    fresh = _cache.get_fresh()
    if fresh is not None:
        return fresh
    try:
        data = await asyncio.to_thread(_fetch_sync, settings)
        _cache.set(data)
        return data
    except Exception:
        stale = _cache.get_any()
        if stale is None:
            return {"next": None, "stale": True}
        return {**stale, "stale": True}