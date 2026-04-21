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
