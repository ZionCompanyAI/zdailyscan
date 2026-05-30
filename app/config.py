from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aliexpress_app_key: str
    aliexpress_app_secret: str
    aliexpress_tracking_id: str
    aliexpress_session_cookies: str | None = None
    telegram_bot_token: str
    mc_api_key: str
    mc_url: str
    usd_brl_rate: float = 5.70
    telegram_chat_id: int = Field(
        default=7041182277, validation_alias="ZDAILYSCAN_TELEGRAM_CHAT_ID"
    )

    dashboard_username: str = "admin"
    dashboard_password: str
    dashboard_session_secret: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
