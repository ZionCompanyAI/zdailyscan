import pytest


def _set_required(monkeypatch, **overrides):
    defaults = {
        "ALIEXPRESS_APP_KEY": "x",
        "ALIEXPRESS_APP_SECRET": "x",
        "ALIEXPRESS_TRACKING_ID": "x",
        "TELEGRAM_BOT_TOKEN": "x",
        "MC_API_KEY": "x",
        "MC_URL": "http://mc.example.com",
        "DASHBOARD_PASSWORD": "x",
        "DASHBOARD_SESSION_SECRET": "x",
    }
    for k, v in {**defaults, **overrides}.items():
        monkeypatch.setenv(k, v)


def test_settings_loads_from_env(monkeypatch):
    _set_required(
        monkeypatch,
        ALIEXPRESS_APP_KEY="key123",
        ALIEXPRESS_APP_SECRET="secret123",
        ALIEXPRESS_TRACKING_ID="track123",
        TELEGRAM_BOT_TOKEN="tg:token",
        MC_API_KEY="mc_key",
        MC_URL="https://mc.example.com",
    )

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
        "ALIEXPRESS_APP_KEY",
        "ALIEXPRESS_APP_SECRET",
        "ALIEXPRESS_TRACKING_ID",
        "TELEGRAM_BOT_TOKEN",
        "MC_API_KEY",
        "MC_URL",
    ]:
        monkeypatch.delenv(key, raising=False)

    from app.config import Settings

    with pytest.raises(Exception):
        Settings()


def test_telegram_chat_id_default(monkeypatch):
    _set_required(monkeypatch)
    monkeypatch.delenv("ZDAILYSCAN_TELEGRAM_CHAT_ID", raising=False)

    from app.config import Settings

    s = Settings()
    assert s.telegram_chat_id == 7041182277


def test_telegram_chat_id_from_env(monkeypatch):
    _set_required(monkeypatch)
    monkeypatch.setenv("ZDAILYSCAN_TELEGRAM_CHAT_ID", "9999999999")

    from app.config import Settings

    s = Settings()
    assert s.telegram_chat_id == 9999999999


def test_aliexpress_credentials_default_to_none(monkeypatch):
    _set_required(monkeypatch)
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)

    from app.config import Settings

    s = Settings()
    assert s.aliexpress_session_cookies == ""


def test_aliexpress_credentials_load_from_env(monkeypatch):
    _set_required(monkeypatch)
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", "session=abc123; token=xyz")

    from app.config import Settings

    s = Settings()
    assert s.aliexpress_session_cookies == "session=abc123; token=xyz"
