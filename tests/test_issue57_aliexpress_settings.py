"""Tests for TASK-057 (updated by TASK-072): AliExpress session cookies in settings page.

Originally tested username/password form. Updated to test SESSION_COOKIES textarea
after issue #72 replaced credential-based auth with cookie session injection.
"""

import os

os.environ.setdefault("ALIEXPRESS_APP_KEY", "test")
os.environ.setdefault("ALIEXPRESS_APP_SECRET", "test")
os.environ.setdefault("ALIEXPRESS_TRACKING_ID", "testtrack")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("MC_API_KEY", "test")
os.environ.setdefault("MC_URL", "http://localhost")
os.environ.setdefault("DASHBOARD_USERNAME", "admin")
os.environ.setdefault("DASHBOARD_PASSWORD", "secret")
os.environ.setdefault("DASHBOARD_SESSION_SECRET", "test-secret-key")


def _make_client(monkeypatch):
    monkeypatch.setenv("DASHBOARD_USERNAME", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    monkeypatch.setenv("DASHBOARD_SESSION_SECRET", "test-secret-key")
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app, follow_redirects=False)


def _signed_cookie(username: str = "admin") -> str:
    from itsdangerous import URLSafeSerializer

    s = URLSafeSerializer("test-secret-key", salt="session")
    return s.dumps({"user": username})


# ---------------------------------------------------------------------------
# 1. GET /dashboard/settings — AliExpress card shows SESSION_COOKIES
# ---------------------------------------------------------------------------


def test_settings_has_session_cookies_indicator(monkeypatch):
    """Settings page deve conter ALIEXPRESS_SESSION_COOKIES no HTML."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "SESSION_COOKIES" in resp.text or "session_cookies" in resp.text


def test_settings_shows_empty_status_when_cookies_unset(monkeypatch):
    """Quando ALIEXPRESS_SESSION_COOKIES não configurado, status indica vazio."""
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "○" in resp.text or "Vazio" in resp.text


def test_settings_shows_filled_status_when_cookies_set(monkeypatch):
    """Quando ALIEXPRESS_SESSION_COOKIES configurado, status indica preenchido."""
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", '{"ali_apache_id":"test"}')
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "●" in resp.text or "Preenchido" in resp.text


def test_settings_aliexpress_form_posts_to_dashboard_settings(monkeypatch):
    """Form AliExpress deve ter action POST para /dashboard/settings."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert 'action="/dashboard/settings"' in resp.text


def test_settings_aliexpress_does_not_expose_cookie_values(monkeypatch):
    """Settings não deve exibir os valores dos cookies no HTML."""
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", '{"secret_cookie":"supersecretvalue"}')
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "supersecretvalue" not in resp.text


# ---------------------------------------------------------------------------
# 2. POST /dashboard/settings — save session cookies
# ---------------------------------------------------------------------------


def test_post_settings_without_auth_redirects(monkeypatch):
    """POST /dashboard/settings sem auth redireciona para /login."""
    client = _make_client(monkeypatch)
    resp = client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": '{"test":"val"}'},
    )
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_post_settings_with_auth_redirects_to_settings(monkeypatch):
    """POST /dashboard/settings com auth redireciona para /dashboard/settings."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": '{"ali_apache_id":"abc"}'},
        cookies={"session": cookie},
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dashboard/settings"


def test_post_settings_saves_session_cookies_to_env(monkeypatch):
    """POST /dashboard/settings salva ALIEXPRESS_SESSION_COOKIES em os.environ."""
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    payload = '{"ali_apache_id":"abc","_tb_token_":"xyz"}'
    client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": payload},
        cookies={"session": cookie},
    )
    assert os.environ.get("ALIEXPRESS_SESSION_COOKIES") == payload


def test_post_settings_empty_field_does_not_overwrite(monkeypatch):
    """POST com campo vazio não sobrescreve ALIEXPRESS_SESSION_COOKIES existente."""
    existing = '{"ali_apache_id":"existing"}'
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", existing)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": ""},
        cookies={"session": cookie},
    )
    assert os.environ.get("ALIEXPRESS_SESSION_COOKIES") == existing
