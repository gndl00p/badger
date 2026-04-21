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