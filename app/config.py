import os

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_AUTH_BUS_TOKEN_PATH = "/tokens/mercadolibre"
_AUTH_BUS_DEFAULT_URL = "https://auth-bus.zioncompanyai.com.br"
_AUTH_BUS_USER_AGENT = "ZionCompanyAI/1.0"


async def get_ml_access_token() -> str:
    """Try auth-bus first; fall back to ML_USER_ACCESS_TOKEN env var."""
    bus_url = os.environ.get("AUTH_BUS_URL", _AUTH_BUS_DEFAULT_URL)
    bus_key = os.environ.get("AUTH_BUS_API_KEY", "")
    if bus_key:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{bus_url}{_AUTH_BUS_TOKEN_PATH}",
                    headers={
                        "x-api-key": bus_key,
                        "User-Agent": _AUTH_BUS_USER_AGENT,
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json().get("access_token", "")
        except Exception:
            pass
    return os.environ.get("ML_USER_ACCESS_TOKEN", "")


class Settings(BaseSettings):
    aliexpress_app_key: str
    aliexpress_app_secret: str
    aliexpress_tracking_id: str
    aliexpress_session_cookies: str = ""
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
