import pytest


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("ALIEXPRESS_APP_KEY", "key123")
    monkeypatch.setenv("ALIEXPRESS_APP_SECRET", "secret123")
    monkeypatch.setenv("ALIEXPRESS_TRACKING_ID", "track123")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tg:token")
    monkeypatch.setenv("MC_API_KEY", "mc_key")
    monkeypatch.setenv("MC_URL", "https://mc.example.com")

    from app.config import Settings
    s = Settings()
    assert s.aliexpress_app_key == "key123"
    assert s.aliexpress_app_secret == "secret123"
    assert s.aliexpress_tracking_id == "track123"
    assert s.telegram_bot_token == "tg:token"
    assert s.mc_api_key == "mc_key"
    assert s.mc_url == "https://mc.example.com"


def test_settings_missing_required_raises(monkeypatch):
    for key in [
        "ALIEXPRESS_APP_KEY", "ALIEXPRESS_APP_SECRET", "ALIEXPRESS_TRACKING_ID",
        "TELEGRAM_BOT_TOKEN", "MC_API_KEY", "MC_URL",
    ]:
        monkeypatch.delenv(key, raising=False)

    from app.config import Settings
    with pytest.raises(Exception):
        Settings()
