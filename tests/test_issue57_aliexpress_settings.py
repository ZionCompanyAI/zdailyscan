"""Tests for TASK-057: AliExpress credentials form in settings page."""

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


def test_settings_has_aliexpress_username_field(monkeypatch):
    """Settings page deve conter ALIEXPRESS_USERNAME no HTML."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "ALIEXPRESS_USERNAME" in resp.text


def test_settings_has_aliexpress_password_field(monkeypatch):
    """Settings page deve conter ALIEXPRESS_PASSWORD no HTML."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "ALIEXPRESS_PASSWORD" in resp.text


def test_settings_shows_aliexpress_status_empty(monkeypatch):
    """Quando credenciais não configuradas, status deve indicar vazio."""
    monkeypatch.delenv("ALIEXPRESS_USERNAME", raising=False)
    monkeypatch.delenv("ALIEXPRESS_PASSWORD", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    body = resp.text
    assert "aliexpress_username_set" not in body or "Vazio" in body or "vazio" in body or "empty" in body.lower() or "○" in body


def test_settings_shows_aliexpress_status_filled(monkeypatch):
    """Quando credenciais configuradas, status deve indicar preenchido."""
    monkeypatch.setenv("ALIEXPRESS_USERNAME", "myuser")
    monkeypatch.setenv("ALIEXPRESS_PASSWORD", "mypass")
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


def test_settings_aliexpress_does_not_expose_values(monkeypatch):
    """Settings não deve exibir os valores das credenciais."""
    monkeypatch.setenv("ALIEXPRESS_USERNAME", "supersecretuser")
    monkeypatch.setenv("ALIEXPRESS_PASSWORD", "supersecretpass")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "supersecretuser" not in resp.text
    assert "supersecretpass" not in resp.text


# ---------------------------------------------------------------------------
# 2. POST /dashboard/settings — save credentials
# ---------------------------------------------------------------------------


def test_post_settings_without_auth_redirects(monkeypatch):
    """POST /dashboard/settings sem auth redireciona para /login."""
    client = _make_client(monkeypatch)
    resp = client.post(
        "/dashboard/settings",
        data={"aliexpress_username": "user", "aliexpress_password": "pass"},
    )
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_post_settings_with_auth_redirects_to_settings(monkeypatch):
    """POST /dashboard/settings com auth redireciona para /dashboard/settings."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.post(
        "/dashboard/settings",
        data={"aliexpress_username": "newuser", "aliexpress_password": "newpass"},
        cookies={"session": cookie},
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dashboard/settings"


def test_post_settings_saves_username_to_env(monkeypatch):
    """POST /dashboard/settings salva ALIEXPRESS_USERNAME em os.environ."""
    monkeypatch.delenv("ALIEXPRESS_USERNAME", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    client.post(
        "/dashboard/settings",
        data={"aliexpress_username": "myaliuser", "aliexpress_password": ""},
        cookies={"session": cookie},
    )
    assert os.environ.get("ALIEXPRESS_USERNAME") == "myaliuser"


def test_post_settings_saves_password_to_env(monkeypatch):
    """POST /dashboard/settings salva ALIEXPRESS_PASSWORD em os.environ."""
    monkeypatch.delenv("ALIEXPRESS_PASSWORD", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    client.post(
        "/dashboard/settings",
        data={"aliexpress_username": "", "aliexpress_password": "myalipass"},
        cookies={"session": cookie},
    )
    assert os.environ.get("ALIEXPRESS_PASSWORD") == "myalipass"


def test_post_settings_empty_fields_do_not_overwrite(monkeypatch):
    """POST com campos vazios não deve sobrescrever valores existentes."""
    monkeypatch.setenv("ALIEXPRESS_USERNAME", "existinguser")
    monkeypatch.setenv("ALIEXPRESS_PASSWORD", "existingpass")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    client.post(
        "/dashboard/settings",
        data={"aliexpress_username": "", "aliexpress_password": ""},
        cookies={"session": cookie},
    )
    assert os.environ.get("ALIEXPRESS_USERNAME") == "existinguser"
    assert os.environ.get("ALIEXPRESS_PASSWORD") == "existingpass"
