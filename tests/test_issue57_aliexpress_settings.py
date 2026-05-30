"""Tests for TASK-057: AliExpress session cookies form in settings page."""

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
# 1. GET /dashboard/settings — AliExpress card in template
# ---------------------------------------------------------------------------


def test_settings_has_aliexpress_session_cookies_field(monkeypatch):
    """Settings page deve conter textarea de session_cookies no HTML."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "aliexpress_session_cookies" in resp.text


def test_settings_has_aliexpress_credentials_section(monkeypatch):
    """Settings page deve conter seção AliExpress Credentials."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "AliExpress" in resp.text


def test_settings_shows_aliexpress_status_empty(monkeypatch):
    """Quando cookies não configurados, status deve indicar vazio."""
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    body = resp.text
    assert "Vazio" in body or "vazio" in body or "empty" in body.lower() or "○" in body


def test_settings_shows_aliexpress_status_filled(monkeypatch):
    """Quando cookies configurados, status deve indicar preenchido."""
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", '[{"name":"sid","value":"abc"}]')
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    body = resp.text
    assert "Preenchido" in body or "preenchido" in body or "●" in body or "filled" in body.lower()


def test_settings_aliexpress_form_posts_to_dashboard_settings(monkeypatch):
    """Form AliExpress deve ter action POST para /dashboard/settings."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert 'action="/dashboard/settings"' in resp.text or "action=\"/dashboard/settings\"" in resp.text


def test_settings_aliexpress_does_not_expose_cookie_values(monkeypatch):
    """Settings não deve exibir os valores dos cookies na página quando vazio."""
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "supersecretcookie" not in resp.text


# ---------------------------------------------------------------------------
# 2. POST /dashboard/settings — save session cookies
# ---------------------------------------------------------------------------


def test_post_settings_without_auth_redirects(monkeypatch):
    """POST /dashboard/settings sem auth redireciona para /login."""
    client = _make_client(monkeypatch)
    resp = client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": '[{"name":"sid","value":"abc"}]'},
    )
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_post_settings_with_auth_redirects_to_settings(monkeypatch):
    """POST /dashboard/settings com auth redireciona para /dashboard/settings."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": '[{"name":"sid","value":"abc"}]'},
        cookies={"session": cookie},
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dashboard/settings"


def test_post_settings_saves_session_cookies_to_env(monkeypatch):
    """POST /dashboard/settings salva ALIEXPRESS_SESSION_COOKIES em os.environ."""
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    cookies_json = '[{"name":"sid","value":"mytoken"}]'
    client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": cookies_json},
        cookies={"session": cookie},
    )
    assert os.environ.get("ALIEXPRESS_SESSION_COOKIES") == cookies_json


def test_post_settings_empty_cookies_do_not_overwrite(monkeypatch):
    """POST com cookies vazios não deve sobrescrever valor existente."""
    existing = '[{"name":"sid","value":"existing"}]'
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", existing)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    client.post(
        "/dashboard/settings",
        data={"aliexpress_session_cookies": ""},
        cookies={"session": cookie},
    )
    assert os.environ.get("ALIEXPRESS_SESSION_COOKIES") == existing
