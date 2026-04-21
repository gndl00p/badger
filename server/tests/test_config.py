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
