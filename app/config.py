from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aliexpress_app_key: str
    aliexpress_app_secret: str
    aliexpress_tracking_id: str
    telegram_bot_token: str
    mc_api_key: str
    mc_url: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
