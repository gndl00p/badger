# Badger Aggregator Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI aggregator service at `~/code/badger/server/` that exposes `GET /badge.json` with token-gated access, fetches weather (open-meteo), next calendar event (Google), Zoho Desk open ticket count, and Zoho CRM tasks-due-today in parallel, with per-tile TTL caching and stale-on-error fallback, then deploy it as a user systemd unit.

**Architecture:** FastAPI async app. Each upstream lives in its own module under `server/upstreams/` with a private `_fetch()` coroutine plus a public `get()` coroutine that wraps `_fetch` in a per-upstream `TTLCache`. On fetch exception the public `get()` falls back to the last successful value and marks the tile `"stale": True`. The endpoint awaits all four upstreams concurrently via `asyncio.gather` with a 2 s HTTP timeout ceiling. Secrets and lat/long come from a `.env` file loaded by `pydantic-settings`.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, httpx (async), pydantic v2, pydantic-settings, google-api-python-client + google-auth, pytest + pytest-asyncio + respx, systemd user unit.

---

## File Structure

Created (all paths relative to `~/code/badger/`):

| File | Responsibility |
| --- | --- |
| `server/__init__.py` | Marks package |
| `server/config.py` | `Settings` model loading from `.env` (pydantic-settings) |
| `server/schemas.py` | Pydantic response models for `/badge.json` |
| `server/cache.py` | `TTLCache` helper shared by all upstreams |
| `server/auth.py` | FastAPI dependency enforcing `X-Badge-Token` header |
| `server/upstreams/__init__.py` | Marks package |
| `server/upstreams/weather.py` | open-meteo client + WMO code → icon mapping |
| `server/upstreams/calendar.py` | Google Calendar next-event lookup (sync lib via `asyncio.to_thread`) |
| `server/upstreams/zoho_desk.py` | Zoho Desk access-token exchange + open tickets count |
| `server/upstreams/zoho_crm.py` | Zoho CRM access-token exchange + COQL for today's tasks |
| `server/app.py` | FastAPI app wiring the endpoint + CORS-free, LAN-only |
| `server/requirements.txt` | Runtime deps (pinned) |
| `server/requirements-dev.txt` | Test deps |
| `server/.env.example` | Example config, checked in |
| `server/badger.service` | Systemd user unit |
| `server/README.md` | Run + deploy instructions |
| `server/tests/__init__.py` | Marks package |
| `server/tests/conftest.py` | Shared fixtures (settings override, httpx client) |
| `server/tests/test_auth.py` | Token enforcement |
| `server/tests/test_cache.py` | `TTLCache` behaviour |
| `server/tests/test_weather.py` | Weather fetch + mapping + stale fallback |
| `server/tests/test_calendar.py` | Calendar fetch + stale fallback |
| `server/tests/test_zoho_desk.py` | Desk fetch + token refresh + stale fallback |
| `server/tests/test_zoho_crm.py` | CRM fetch + COQL shape + stale fallback |
| `server/tests/test_endpoint.py` | Integration: endpoint composes all four tiles |
| `server/tests/fixtures/open_meteo_sunny.json` | Recorded open-meteo response |
| `server/tests/fixtures/zoho_oauth_token.json` | Recorded Zoho token response |
| `server/tests/fixtures/zoho_desk_count.json` | Recorded Desk count response |
| `server/tests/fixtures/zoho_crm_coql.json` | Recorded COQL response |

---

## Task 1: Project scaffolding

**Files:**
- Create: `server/__init__.py`
- Create: `server/requirements.txt`
- Create: `server/requirements-dev.txt`
- Create: `server/.env.example`
- Create: `server/README.md`
- Create: `server/tests/__init__.py`
- Create: `server/tests/conftest.py`

- [ ] **Step 1: Create the venv and empty package files**

```bash
cd ~/code/badger
python3 -m venv server/.venv
source server/.venv/bin/activate
touch server/__init__.py server/tests/__init__.py
```

- [ ] **Step 2: Write `server/requirements.txt`**

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
httpx==0.27.2
pydantic==2.9.2
pydantic-settings==2.6.1
google-api-python-client==2.149.0
google-auth==2.35.0
```

- [ ] **Step 3: Write `server/requirements-dev.txt`**

```
-r requirements.txt
pytest==8.3.3
pytest-asyncio==0.24.0
respx==0.21.1
freezegun==1.5.1
```

- [ ] **Step 4: Install dev deps**

Run: `pip install -r server/requirements-dev.txt`
Expected: all packages install without error.

- [ ] **Step 5: Write `server/.env.example`**

```
# Shared
BADGE_TOKEN=replace-me-with-a-long-random-string

# Weather (open-meteo, no key)
WEATHER_LATITUDE=30.2672
WEATHER_LONGITUDE=-97.7431

# Google Calendar
GOOGLE_SERVICE_ACCOUNT_JSON=/home/gndl00p/.config/badger/google-sa.json
GOOGLE_CALENDAR_ID=philip@teamrobb.com

# Zoho (shared accounts host)
ZOHO_ACCOUNTS_HOST=https://accounts.zoho.com

# Zoho Desk
ZOHODESK_API_HOST=https://desk.zoho.com
ZOHODESK_CLIENT_ID=
ZOHODESK_CLIENT_SECRET=
ZOHODESK_REFRESH_TOKEN=
ZOHODESK_ORG_ID=

# Zoho CRM
ZOHOCRM_API_HOST=https://www.zohoapis.com
ZOHOCRM_CLIENT_ID=
ZOHOCRM_CLIENT_SECRET=
ZOHOCRM_REFRESH_TOKEN=
ZOHOCRM_USER_ID=
```

- [ ] **Step 6: Write `server/README.md`**

```markdown
# Badger Aggregator

FastAPI service that feeds the Badger 2040 W desk-mode dashboard.

## Run (dev)

    cd ~/code/badger
    source server/.venv/bin/activate
    cp server/.env.example server/.env   # then fill in secrets
    uvicorn server.app:app --host 127.0.0.1 --port 8088 --env-file server/.env

## Test

    cd ~/code/badger
    source server/.venv/bin/activate
    pytest server/tests -v

## Deploy (user systemd)

    mkdir -p ~/.config/systemd/user
    cp server/badger.service ~/.config/systemd/user/badger.service
    systemctl --user daemon-reload
    systemctl --user enable --now badger
    systemctl --user status badger
```

- [ ] **Step 7: Write `server/tests/conftest.py`** (placeholder imported by later tasks)

```python
import pytest


@pytest.fixture
def fixtures_dir():
    from pathlib import Path

    return Path(__file__).parent / "fixtures"
```

- [ ] **Step 8: Confirm pytest discovers the empty suite**

Run: `cd ~/code/badger && pytest server/tests -v`
Expected: `no tests ran in ...` (exit 5 is fine).

- [ ] **Step 9: Commit**

```bash
cd ~/code/badger
git add server/__init__.py server/tests/__init__.py server/tests/conftest.py \
        server/requirements.txt server/requirements-dev.txt \
        server/.env.example server/README.md
git commit -m "chore(server): scaffold aggregator package and tooling"
```

(Do not commit `server/.venv/`. If it ended up staged, add a `.gitignore` line for `server/.venv/` before committing.)

---

## Task 2: Settings model

**Files:**
- Create: `server/config.py`
- Test: `server/tests/test_config.py`

- [ ] **Step 1: Write `server/tests/test_config.py`**

```python
from server.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("BADGE_TOKEN", "abc")
    monkeypatch.setenv("WEATHER_LATITUDE", "30.27")
    monkeypatch.setenv("WEATHER_LONGITUDE", "-97.74")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/tmp/sa.json")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "x@example.com")
    monkeypatch.setenv("ZOHODESK_CLIENT_ID", "dcid")
    monkeypatch.setenv("ZOHODESK_CLIENT_SECRET", "dcs")
    monkeypatch.setenv("ZOHODESK_REFRESH_TOKEN", "drt")
    monkeypatch.setenv("ZOHODESK_ORG_ID", "42")
    monkeypatch.setenv("ZOHOCRM_CLIENT_ID", "ccid")
    monkeypatch.setenv("ZOHOCRM_CLIENT_SECRET", "ccs")
    monkeypatch.setenv("ZOHOCRM_REFRESH_TOKEN", "crt")
    monkeypatch.setenv("ZOHOCRM_USER_ID", "99")

    s = Settings()

    assert s.badge_token == "abc"
    assert s.weather_latitude == 30.27
    assert s.weather_longitude == -97.74
    assert s.google_service_account_json == "/tmp/sa.json"
    assert s.zohodesk_org_id == "42"
    assert s.zohocrm_user_id == "99"
    assert s.zoho_accounts_host == "https://accounts.zoho.com"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/code/badger && pytest server/tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'server.config'`.

- [ ] **Step 3: Write `server/config.py`**

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    badge_token: str = Field(..., alias="BADGE_TOKEN")

    weather_latitude: float = Field(..., alias="WEATHER_LATITUDE")
    weather_longitude: float = Field(..., alias="WEATHER_LONGITUDE")

    google_service_account_json: str = Field(..., alias="GOOGLE_SERVICE_ACCOUNT_JSON")
    google_calendar_id: str = Field(..., alias="GOOGLE_CALENDAR_ID")

    zoho_accounts_host: str = Field("https://accounts.zoho.com", alias="ZOHO_ACCOUNTS_HOST")

    zohodesk_api_host: str = Field("https://desk.zoho.com", alias="ZOHODESK_API_HOST")
    zohodesk_client_id: str = Field(..., alias="ZOHODESK_CLIENT_ID")
    zohodesk_client_secret: str = Field(..., alias="ZOHODESK_CLIENT_SECRET")
    zohodesk_refresh_token: str = Field(..., alias="ZOHODESK_REFRESH_TOKEN")
    zohodesk_org_id: str = Field(..., alias="ZOHODESK_ORG_ID")

    zohocrm_api_host: str = Field("https://www.zohoapis.com", alias="ZOHOCRM_API_HOST")
    zohocrm_client_id: str = Field(..., alias="ZOHOCRM_CLIENT_ID")
    zohocrm_client_secret: str = Field(..., alias="ZOHOCRM_CLIENT_SECRET")
    zohocrm_refresh_token: str = Field(..., alias="ZOHOCRM_REFRESH_TOKEN")
    zohocrm_user_id: str = Field(..., alias="ZOHOCRM_USER_ID")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/code/badger && pytest server/tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server/config.py server/tests/test_config.py
git commit -m "feat(server): Settings model loaded from .env"
```

---

## Task 3: TTLCache helper

**Files:**
- Create: `server/cache.py`
- Test: `server/tests/test_cache.py`

- [ ] **Step 1: Write `server/tests/test_cache.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest server/tests/test_cache.py -v`
Expected: 4 failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `server/cache.py`**

```python
import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl = ttl_seconds
        self._entry: tuple[float, Any] | None = None

    def set(self, value: Any) -> None:
        self._entry = (time.monotonic(), value)

    def get_fresh(self) -> Any | None:
        if self._entry is None:
            return None
        ts, value = self._entry
        if time.monotonic() - ts < self.ttl:
            return value
        return None

    def get_any(self) -> Any | None:
        if self._entry is None:
            return None
        return self._entry[1]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest server/tests/test_cache.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cache.py server/tests/test_cache.py
git commit -m "feat(server): TTLCache for per-upstream data caching"
```

---

## Task 4: Response schemas

**Files:**
- Create: `server/schemas.py`
- Test: `server/tests/test_schemas.py`

- [ ] **Step 1: Write `server/tests/test_schemas.py`**

```python
from server.schemas import BadgePayload, WeatherTile, CalendarTile, DeskTile, CrmTile, NextEvent


def test_payload_round_trip():
    p = BadgePayload(
        generated_at="2026-04-21T10:00:00-05:00",
        weather=WeatherTile(temp_f=72, summary="sunny", icon="sun"),
        calendar=CalendarTile(next=NextEvent(start="2026-04-21T15:00:00-05:00", title="Standup")),
        desk=DeskTile(open_tickets=4),
        crm=CrmTile(tasks_due_today=2),
    )
    data = p.model_dump()
    assert data["weather"]["temp_f"] == 72
    assert data["weather"]["stale"] is False
    assert data["calendar"]["next"]["title"] == "Standup"
    assert data["desk"]["open_tickets"] == 4
    assert data["crm"]["tasks_due_today"] == 2


def test_calendar_tile_allows_null_next():
    t = CalendarTile(next=None)
    assert t.model_dump()["next"] is None


def test_stale_defaults_false():
    assert WeatherTile(temp_f=None, summary="unknown", icon="none").model_dump()["stale"] is False
    assert WeatherTile(temp_f=None, summary="unknown", icon="none", stale=True).model_dump()["stale"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest server/tests/test_schemas.py -v`
Expected: 3 failures with `ModuleNotFoundError`.

- [ ] **Step 3: Write `server/schemas.py`**

```python
from pydantic import BaseModel


class WeatherTile(BaseModel):
    temp_f: int | None
    summary: str
    icon: str
    stale: bool = False


class NextEvent(BaseModel):
    start: str
    title: str


class CalendarTile(BaseModel):
    next: NextEvent | None = None
    stale: bool = False


class DeskTile(BaseModel):
    open_tickets: int
    stale: bool = False


class CrmTile(BaseModel):
    tasks_due_today: int
    stale: bool = False


class BadgePayload(BaseModel):
    generated_at: str
    weather: WeatherTile
    calendar: CalendarTile
    desk: DeskTile
    crm: CrmTile
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest server/tests/test_schemas.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add server/schemas.py server/tests/test_schemas.py
git commit -m "feat(server): pydantic response schemas for /badge.json"
```

---

## Task 5: Token auth dependency

**Files:**
- Create: `server/auth.py`
- Test: `server/tests/test_auth.py`

- [ ] **Step 1: Write `server/tests/test_auth.py`**

```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.auth import require_badge_token
from server.config import Settings


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("BADGE_TOKEN", "s3cret")
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

    app = FastAPI()

    @app.get("/ping", dependencies=[require_badge_token(Settings())])
    def ping():
        return {"ok": True}

    return app


def test_missing_token_is_401(app):
    r = TestClient(app).get("/ping")
    assert r.status_code == 401


def test_wrong_token_is_401(app):
    r = TestClient(app).get("/ping", headers={"X-Badge-Token": "nope"})
    assert r.status_code == 401


def test_correct_token_is_200(app):
    r = TestClient(app).get("/ping", headers={"X-Badge-Token": "s3cret"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest server/tests/test_auth.py -v`
Expected: 3 failures with `ModuleNotFoundError: No module named 'server.auth'`.

- [ ] **Step 3: Write `server/auth.py`**

```python
from fastapi import Depends, Header, HTTPException, status

from server.config import Settings


def require_badge_token(settings: Settings):
    def _check(x_badge_token: str | None = Header(default=None)):
        if x_badge_token != settings.badge_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad token")

    return Depends(_check)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest server/tests/test_auth.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add server/auth.py server/tests/test_auth.py
git commit -m "feat(server): X-Badge-Token header auth dependency"
```

---

## Task 6: Weather upstream

**Files:**
- Create: `server/upstreams/__init__.py`
- Create: `server/upstreams/weather.py`
- Create: `server/tests/fixtures/open_meteo_sunny.json`
- Test: `server/tests/test_weather.py`

- [ ] **Step 1: Create package marker**

```bash
touch ~/code/badger/server/upstreams/__init__.py
```

- [ ] **Step 2: Write `server/tests/fixtures/open_meteo_sunny.json`**

```json
{
  "latitude": 30.27,
  "longitude": -97.74,
  "current": {
    "time": "2026-04-21T15:00",
    "temperature_2m": 72.4,
    "weather_code": 1
  },
  "current_units": {
    "temperature_2m": "°F",
    "weather_code": "wmo code"
  }
}
```

- [ ] **Step 3: Write `server/tests/test_weather.py`**

```python
import json

import httpx
import pytest
import respx

from server.config import Settings
from server.upstreams import weather


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("BADGE_TOKEN", "t")
    monkeypatch.setenv("WEATHER_LATITUDE", "30.27")
    monkeypatch.setenv("WEATHER_LONGITUDE", "-97.74")
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
    weather._cache.__init__(ttl_seconds=weather._cache.ttl)  # reset between tests


@pytest.mark.asyncio
async def test_weather_happy_path(settings, fixtures_dir):
    payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())

    with respx.mock(base_url="https://api.open-meteo.com") as m:
        m.get("/v1/forecast").mock(return_value=httpx.Response(200, json=payload))

        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)

    assert result["temp_f"] == 72
    assert result["icon"] == "sun"
    assert "sunny" in result["summary"].lower() or "clear" in result["summary"].lower()
    assert result["stale"] is False


@pytest.mark.asyncio
async def test_weather_cached_within_ttl(settings, fixtures_dir):
    payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())

    with respx.mock(base_url="https://api.open-meteo.com") as m:
        route = m.get("/v1/forecast").mock(return_value=httpx.Response(200, json=payload))

        async with httpx.AsyncClient() as client:
            await weather.get(client, settings)
            await weather.get(client, settings)

    assert route.call_count == 1


@pytest.mark.asyncio
async def test_weather_stale_fallback_on_error(settings, fixtures_dir):
    payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())

    with respx.mock(base_url="https://api.open-meteo.com") as m:
        m.get("/v1/forecast").mock(return_value=httpx.Response(200, json=payload))
        async with httpx.AsyncClient() as client:
            await weather.get(client, settings)

    # Force cache miss by expiring TTL, then fail upstream.
    weather._cache._entry = (weather._cache._entry[0] - 1e6, weather._cache._entry[1])

    with respx.mock(base_url="https://api.open-meteo.com") as m:
        m.get("/v1/forecast").mock(return_value=httpx.Response(500))
        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)

    assert result["stale"] is True
    assert result["temp_f"] == 72


@pytest.mark.asyncio
async def test_weather_default_when_never_succeeded(settings):
    with respx.mock(base_url="https://api.open-meteo.com") as m:
        m.get("/v1/forecast").mock(return_value=httpx.Response(500))
        async with httpx.AsyncClient() as client:
            result = await weather.get(client, settings)

    assert result["stale"] is True
    assert result["temp_f"] is None
    assert result["icon"] == "none"
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest server/tests/test_weather.py -v`
Expected: 4 failures with `ModuleNotFoundError: No module named 'server.upstreams.weather'`.

- [ ] **Step 5: Write `server/upstreams/weather.py`**

```python
import httpx

from server.cache import TTLCache
from server.config import Settings

_cache = TTLCache(ttl_seconds=60)

_WMO = {
    0: ("clear", "sun"),
    1: ("sunny", "sun"),
    2: ("partly cloudy", "cloud"),
    3: ("cloudy", "cloud"),
    45: ("fog", "fog"),
    48: ("fog", "fog"),
    51: ("drizzle", "rain"),
    53: ("drizzle", "rain"),
    55: ("drizzle", "rain"),
    61: ("rain", "rain"),
    63: ("rain", "rain"),
    65: ("heavy rain", "rain"),
    66: ("freezing rain", "rain"),
    67: ("freezing rain", "rain"),
    71: ("snow", "snow"),
    73: ("snow", "snow"),
    75: ("heavy snow", "snow"),
    77: ("snow grains", "snow"),
    80: ("showers", "rain"),
    81: ("showers", "rain"),
    82: ("heavy showers", "rain"),
    85: ("snow showers", "snow"),
    86: ("snow showers", "snow"),
    95: ("thunderstorm", "storm"),
    96: ("thunderstorm", "storm"),
    99: ("thunderstorm", "storm"),
}


def _parse(payload: dict) -> dict:
    cur = payload["current"]
    code = int(cur["weather_code"])
    summary, icon = _WMO.get(code, ("unknown", "none"))
    return {
        "temp_f": int(round(float(cur["temperature_2m"]))),
        "summary": summary,
        "icon": icon,
        "stale": False,
    }


async def _fetch(client: httpx.AsyncClient, settings: Settings) -> dict:
    r = await client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": settings.weather_latitude,
            "longitude": settings.weather_longitude,
            "current": "temperature_2m,weather_code",
            "temperature_unit": "fahrenheit",
        },
        timeout=2.0,
    )
    r.raise_for_status()
    return _parse(r.json())


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
            return {"temp_f": None, "summary": "unknown", "icon": "none", "stale": True}
        return {**stale, "stale": True}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest server/tests/test_weather.py -v`
Expected: 4 passed.

- [ ] **Step 7: Commit**

```bash
git add server/upstreams/__init__.py server/upstreams/weather.py \
        server/tests/test_weather.py server/tests/fixtures/open_meteo_sunny.json
git commit -m "feat(server): weather upstream with TTL cache and stale fallback"
```

---

## Task 7: Calendar upstream

**Files:**
- Create: `server/upstreams/calendar.py`
- Test: `server/tests/test_calendar.py`

- [ ] **Step 1: Write `server/tests/test_calendar.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest server/tests/test_calendar.py -v`
Expected: 5 failures with `ModuleNotFoundError: No module named 'server.upstreams.calendar'`.

- [ ] **Step 3: Write `server/upstreams/calendar.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest server/tests/test_calendar.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add server/upstreams/calendar.py server/tests/test_calendar.py
git commit -m "feat(server): Google Calendar upstream with stale fallback"
```

---

## Task 8: Zoho Desk upstream

**Files:**
- Create: `server/upstreams/zoho_desk.py`
- Create: `server/tests/fixtures/zoho_oauth_token.json`
- Create: `server/tests/fixtures/zoho_desk_count.json`
- Test: `server/tests/test_zoho_desk.py`

- [ ] **Step 1: Write `server/tests/fixtures/zoho_oauth_token.json`**

```json
{
  "access_token": "test-access-token",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

- [ ] **Step 2: Write `server/tests/fixtures/zoho_desk_count.json`**

```json
{ "count": 4 }
```

- [ ] **Step 3: Write `server/tests/test_zoho_desk.py`**

```python
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

    with respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
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
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest server/tests/test_zoho_desk.py -v`
Expected: 4 failures with `ModuleNotFoundError: No module named 'server.upstreams.zoho_desk'`.

- [ ] **Step 5: Write `server/upstreams/zoho_desk.py`**

```python
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest server/tests/test_zoho_desk.py -v`
Expected: 4 passed.

- [ ] **Step 7: Commit**

```bash
git add server/upstreams/zoho_desk.py server/tests/test_zoho_desk.py \
        server/tests/fixtures/zoho_oauth_token.json server/tests/fixtures/zoho_desk_count.json
git commit -m "feat(server): Zoho Desk open-tickets upstream with OAuth refresh"
```

---

## Task 9: Zoho CRM upstream

**Files:**
- Create: `server/upstreams/zoho_crm.py`
- Create: `server/tests/fixtures/zoho_crm_coql.json`
- Test: `server/tests/test_zoho_crm.py`

- [ ] **Step 1: Write `server/tests/fixtures/zoho_crm_coql.json`**

```json
{
  "data": [
    { "id": "11111111" },
    { "id": "22222222" }
  ],
  "info": { "count": 2, "more_records": false }
}
```

- [ ] **Step 2: Write `server/tests/test_zoho_crm.py`**

```python
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

    with respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest server/tests/test_zoho_crm.py -v`
Expected: 4 failures with `ModuleNotFoundError: No module named 'server.upstreams.zoho_crm'`.

- [ ] **Step 4: Write `server/upstreams/zoho_crm.py`**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest server/tests/test_zoho_crm.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add server/upstreams/zoho_crm.py server/tests/test_zoho_crm.py \
        server/tests/fixtures/zoho_crm_coql.json
git commit -m "feat(server): Zoho CRM tasks-due-today COQL upstream"
```

---

## Task 10: App wiring and endpoint

**Files:**
- Create: `server/app.py`
- Test: `server/tests/test_endpoint.py`

- [ ] **Step 1: Write `server/tests/test_endpoint.py`**

```python
import json
from unittest.mock import patch

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from freezegun import freeze_time

from server import app as app_module
from server.upstreams import calendar as cal
from server.upstreams import weather as weather_mod
from server.upstreams import zoho_crm as crm
from server.upstreams import zoho_desk as desk


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("BADGE_TOKEN", "s3cret")
    monkeypatch.setenv("WEATHER_LATITUDE", "30.27")
    monkeypatch.setenv("WEATHER_LONGITUDE", "-97.74")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "/tmp/x")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "x@example.com")
    monkeypatch.setenv("ZOHODESK_CLIENT_ID", "dcid")
    monkeypatch.setenv("ZOHODESK_CLIENT_SECRET", "dcs")
    monkeypatch.setenv("ZOHODESK_REFRESH_TOKEN", "drt")
    monkeypatch.setenv("ZOHODESK_ORG_ID", "42")
    monkeypatch.setenv("ZOHOCRM_CLIENT_ID", "ccid")
    monkeypatch.setenv("ZOHOCRM_CLIENT_SECRET", "ccs")
    monkeypatch.setenv("ZOHOCRM_REFRESH_TOKEN", "crt")
    monkeypatch.setenv("ZOHOCRM_USER_ID", "99")


@pytest.fixture(autouse=True)
def reset_caches():
    for mod in (weather_mod, cal, desk, crm):
        mod._cache.__init__(ttl_seconds=mod._cache.ttl)
    desk._token_cache.__init__(ttl_seconds=desk._token_cache.ttl)
    crm._token_cache.__init__(ttl_seconds=crm._token_cache.ttl)


def _fake_cal_service(items):
    from unittest.mock import MagicMock

    svc = MagicMock()
    svc.events.return_value.list.return_value.execute.return_value = {"items": items}
    return svc


@freeze_time("2026-04-21T10:00:00-05:00")
def test_endpoint_happy_path(fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())
    weather_payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())
    desk_count = json.loads((fixtures_dir / "zoho_desk_count.json").read_text())
    crm_payload = json.loads((fixtures_dir / "zoho_crm_coql.json").read_text())
    cal_items = [{"start": {"dateTime": "2026-04-21T15:00:00-05:00"}, "summary": "Standup"}]

    app = app_module.build_app()
    client = TestClient(app)

    with patch.object(cal, "_build_service", return_value=_fake_cal_service(cal_items)), \
         respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        m.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=weather_payload)
        )
        m.get("https://desk.zoho.com/api/v1/ticketsCount").mock(
            return_value=httpx.Response(200, json=desk_count)
        )
        m.post("https://www.zohoapis.com/crm/v8/coql").mock(
            return_value=httpx.Response(200, json=crm_payload)
        )

        r = client.get("/badge.json", headers={"X-Badge-Token": "s3cret"})

    assert r.status_code == 200
    body = r.json()
    assert body["weather"]["temp_f"] == 72
    assert body["weather"]["icon"] == "sun"
    assert body["weather"]["stale"] is False
    assert body["calendar"]["next"]["title"] == "Standup"
    assert body["desk"]["open_tickets"] == 4
    assert body["crm"]["tasks_due_today"] == 2
    assert "generated_at" in body


def test_endpoint_requires_token():
    app = app_module.build_app()
    r = TestClient(app).get("/badge.json")
    assert r.status_code == 401


def test_endpoint_tile_stale_on_partial_failure(fixtures_dir):
    token = json.loads((fixtures_dir / "zoho_oauth_token.json").read_text())
    weather_payload = json.loads((fixtures_dir / "open_meteo_sunny.json").read_text())
    desk_count = json.loads((fixtures_dir / "zoho_desk_count.json").read_text())

    app = app_module.build_app()
    client = TestClient(app)

    with patch.object(cal, "_build_service", side_effect=RuntimeError("boom")), \
         respx.mock() as m:
        m.post("https://accounts.zoho.com/oauth/v2/token").mock(
            return_value=httpx.Response(200, json=token)
        )
        m.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=weather_payload)
        )
        m.get("https://desk.zoho.com/api/v1/ticketsCount").mock(
            return_value=httpx.Response(200, json=desk_count)
        )
        m.post("https://www.zohoapis.com/crm/v8/coql").mock(
            return_value=httpx.Response(500)
        )

        r = client.get("/badge.json", headers={"X-Badge-Token": "s3cret"})

    body = r.json()
    assert r.status_code == 200
    assert body["weather"]["stale"] is False
    assert body["calendar"]["stale"] is True
    assert body["desk"]["stale"] is False
    assert body["crm"]["stale"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/badger && pytest server/tests/test_endpoint.py -v`
Expected: failures with `AttributeError: module 'server.app' has no attribute 'build_app'` (or `ModuleNotFoundError`).

- [ ] **Step 3: Write `server/app.py`**

```python
import asyncio
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI

from server.auth import require_badge_token
from server.config import Settings
from server.schemas import BadgePayload, CalendarTile, CrmTile, DeskTile, WeatherTile
from server.upstreams import calendar as cal
from server.upstreams import weather as weather_mod
from server.upstreams import zoho_crm as crm
from server.upstreams import zoho_desk as desk


def build_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title="Badger Aggregator")

    @app.get("/badge.json", response_model=BadgePayload, dependencies=[require_badge_token(settings)])
    async def badge_json():
        async with httpx.AsyncClient(timeout=2.0) as client:
            weather, calendar_, desk_, crm_ = await asyncio.gather(
                weather_mod.get(client, settings),
                cal.get(settings),
                desk.get(client, settings),
                crm.get(client, settings),
            )
        return BadgePayload(
            generated_at=datetime.now(timezone.utc).astimezone().isoformat(),
            weather=WeatherTile(**weather),
            calendar=CalendarTile(**calendar_),
            desk=DeskTile(**desk_),
            crm=CrmTile(**crm_),
        )

    return app


app = build_app()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/badger && pytest server/tests/test_endpoint.py -v`
Expected: 3 passed.

- [ ] **Step 5: Run the full suite**

Run: `cd ~/code/badger && pytest server/tests -v`
Expected: all previous tests still pass (26+ passed total).

- [ ] **Step 6: Commit**

```bash
git add server/app.py server/tests/test_endpoint.py
git commit -m "feat(server): /badge.json endpoint composing all tiles in parallel"
```

---

## Task 11: pytest config for asyncio

**Files:**
- Create: `server/pytest.ini`

- [ ] **Step 1: Write `server/pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 2: Move the run target so `pytest` from `server/` works**

Run: `cd ~/code/badger/server && pytest -v`
Expected: full suite passes when run from `server/`.

- [ ] **Step 3: Commit**

```bash
git add server/pytest.ini
git commit -m "chore(server): pytest config with asyncio_mode=auto"
```

---

## Task 12: Systemd user unit

**Files:**
- Create: `server/badger.service`

- [ ] **Step 1: Write `server/badger.service`**

```ini
[Unit]
Description=Badger 2040 W aggregator service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/code/badger
EnvironmentFile=%h/code/badger/server/.env
ExecStart=%h/code/badger/server/.venv/bin/uvicorn server.app:app --host 127.0.0.1 --port 8088
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
```

- [ ] **Step 2: Validate syntactically on the host (dry parse)**

Run:
```bash
systemd-analyze --user verify ~/code/badger/server/badger.service 2>&1 | tee /tmp/badger-service-verify.log
```
Expected: empty output (or only `[Install] WantedBy=default.target` notices). The unit is not yet linked into `~/.config/systemd/user/`.

- [ ] **Step 3: Commit**

```bash
git add server/badger.service
git commit -m "chore(server): user systemd unit for aggregator"
```

---

## Task 13: Local smoke test

**Files:** none new; verifies everything works end-to-end on the workstation.

- [ ] **Step 1: Fill in a real `server/.env`**

```bash
cp ~/code/badger/server/.env.example ~/code/badger/server/.env
$EDITOR ~/code/badger/server/.env   # set BADGE_TOKEN to a random string, fill Zoho/Google values
```

- [ ] **Step 2: Start the server**

Run:
```bash
cd ~/code/badger
source server/.venv/bin/activate
uvicorn server.app:app --host 127.0.0.1 --port 8088 --env-file server/.env
```
Expected: `Uvicorn running on http://127.0.0.1:8088`, no tracebacks at startup.

- [ ] **Step 3: Hit the endpoint with the wrong token**

Run (new shell):
```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8088/badge.json
```
Expected: `401`.

- [ ] **Step 4: Hit the endpoint with the right token**

Run:
```bash
TOKEN=$(grep ^BADGE_TOKEN ~/code/badger/server/.env | cut -d= -f2)
curl -sS -H "X-Badge-Token: $TOKEN" http://127.0.0.1:8088/badge.json | python3 -m json.tool
```
Expected: JSON with keys `generated_at`, `weather`, `calendar`, `desk`, `crm`. Any tile with a broken integration has `"stale": true` — that's the defined behaviour and is fine for a smoke test.

- [ ] **Step 5: Install and enable the user service**

Run:
```bash
mkdir -p ~/.config/systemd/user
ln -sf ~/code/badger/server/badger.service ~/.config/systemd/user/badger.service
systemctl --user daemon-reload
systemctl --user enable --now badger
systemctl --user status badger
```
Expected: `active (running)`; `journalctl --user -u badger -n 20` shows uvicorn startup with no errors.

- [ ] **Step 6: Reachability from the LAN**

Run (from another host on the trusted VLAN):
```bash
curl -sS -H "X-Badge-Token: <token>" http://endevour.robb.tech:8088/badge.json
```
Expected: same JSON as Step 4. If the LAN reverse proxy strips `X-Badge-Token`, adjust the proxy config (not part of this plan) and retry.

No commit in this task — it's verification only.

---

## Self-Review

**Spec coverage:**
- `/badge.json` endpoint, LAN-only, token-gated → Tasks 5, 10.
- Response shape (`generated_at`, four tiles) → Tasks 4, 10.
- Weather via open-meteo → Task 6.
- Calendar via Google service account, next event within 24 h → Task 7.
- Zoho Desk open requests → Task 8.
- Zoho CRM tasks due today for current user → Task 9.
- Per-upstream TTL caching (60 s weather/calendar, 30 s Zoho) → Tasks 6–9.
- Stale-flag fallback on upstream errors → Tasks 6–9, 10.
- Endpoint never blocks > 2 s → Tasks 6–9 (`timeout=2.0`), 10 (`AsyncClient(timeout=2.0)`).
- Systemd user unit on endevour → Task 12.
- Same pattern as `tgbot.service` — confirmed in Task 12 by using `%h`-rooted paths and `WantedBy=default.target`.
- Deployment under `systemctl --user enable --now badger` → Task 13.

**Placeholder scan:** none — every step has exact code or an exact command.

**Type consistency:** tile dict keys (`temp_f`, `summary`, `icon`, `stale`; `next`, `stale`; `open_tickets`, `stale`; `tasks_due_today`, `stale`) match schemas and are passed into pydantic models via `**kwargs` in Task 10. Cache object names (`_cache`, `_token_cache`) consistent across Zoho modules and test `reset_state` fixtures.

**Open assumptions carried forward from spec:**
- Existing Zoho OAuth apps can be reused (spec: "If they are namespaced per-tool, the aggregator will need its own OAuth client"). If tests pass but live calls 401 during Task 13, revisit client/refresh-token pairing.
- Google service account must have the target calendar shared with its email; Task 13 surfaces this as a `calendar.stale=true` in the payload if misconfigured.
- Port 8088 free — Task 13 Step 2 fails fast with `address already in use` otherwise.
