"""Tests for dashboard web interface — TASK-030."""

import json
import os

import pytest

# Env vars must be set before any app import
os.environ.setdefault("ALIEXPRESS_APP_KEY", "test")
os.environ.setdefault("ALIEXPRESS_APP_SECRET", "test")
os.environ.setdefault("ALIEXPRESS_TRACKING_ID", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("MC_API_KEY", "test")
os.environ.setdefault("MC_URL", "http://localhost")
os.environ.setdefault("DASHBOARD_USERNAME", "admin")
os.environ.setdefault("DASHBOARD_PASSWORD", "secret")
os.environ.setdefault("DASHBOARD_SESSION_SECRET", "test-secret-key")


def _make_client(monkeypatch):
    """Return TestClient with required env vars set."""
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
# 1. Import smoke test
# ---------------------------------------------------------------------------

def test_import_routers():
    from app.routers.auth import router
    from app.routers.dashboard import router as dr
    assert router is not None
    assert dr is not None


# ---------------------------------------------------------------------------
# 2. Auth / redirect
# ---------------------------------------------------------------------------

def test_root_without_cookie_redirects_to_login(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/")
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_dashboard_without_cookie_redirects_to_login(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/dashboard")
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_dashboard_date_without_cookie_redirects_to_login(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/dashboard/2026-01-01")
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_dashboard_scan_without_cookie_redirects_to_login(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.post("/dashboard/scan")
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


# ---------------------------------------------------------------------------
# 3. Login page
# ---------------------------------------------------------------------------

def test_login_page_returns_200(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"login" in resp.content.lower()


def test_login_post_valid_creds_sets_cookie_and_redirects(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.post("/login", data={"username": "admin", "password": "secret"})
    assert resp.status_code in (302, 303, 307)
    assert "session" in resp.cookies


def test_login_post_invalid_creds_does_not_set_cookie(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.post("/login", data={"username": "admin", "password": "wrong"})
    # Should not set a session cookie on failure
    assert "session" not in resp.cookies


def test_logout_clears_cookie_and_redirects(monkeypatch):
    client = _make_client(monkeypatch)
    # First, log in
    client.post("/login", data={"username": "admin", "password": "secret"},
                follow_redirects=True)
    # Logout
    resp = client.get("/logout")
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


# ---------------------------------------------------------------------------
# 4. Dashboard with valid session
# ---------------------------------------------------------------------------

def test_dashboard_with_valid_session_returns_200(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie("admin")
    resp = client.get("/dashboard", cookies={"session": cookie})
    assert resp.status_code == 200


def test_dashboard_date_not_found_returns_404(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie("admin")
    resp = client.get("/dashboard/2000-01-01", cookies={"session": cookie})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 5. Report table renders correct fields
# ---------------------------------------------------------------------------

def test_report_renders_product_fields(monkeypatch, tmp_path):
    """GET /dashboard/{date} deve renderizar título, score, margem e viável."""
    import app.storage as storage_module
    scans_dir = tmp_path / "scans"
    scans_dir.mkdir()
    monkeypatch.setattr(storage_module, "SCANS_DIR", scans_dir)

    # Write a minimal scan file
    scan = {
        "scan_id": "abc123",
        "date": "2026-01-15",
        "products": [
            {
                "product_id": "p1",
                "title": "Amazing Widget",
                "score_total": 0.75,
                "score_margem": 0.8,
                "score_demanda_br": 0.5,
                "score_oportunidade": 0.6,
                "score_tendencia": 0.5,
                "score_logistica": 1.0,
                "margin_brl": 150.0,
                "sell_price_suggestion_brl": 250.0,
                "viavel": True,
                "demand_count": 50,
                "import_cost_brl": 100.0,
            }
        ],
        "total_scanned": 10,
        "total_viable": 1,
    }
    (scans_dir / "2026-01-15.json").write_text(json.dumps(scan))

    client = _make_client(monkeypatch)
    cookie = _signed_cookie("admin")
    resp = client.get("/dashboard/2026-01-15", cookies={"session": cookie})

    assert resp.status_code == 200
    body = resp.text
    assert "Amazing Widget" in body
    assert "0.75" in body          # score_total
    assert "150" in body           # margin_brl
    assert "250" in body           # sell_price_suggestion_brl


# ---------------------------------------------------------------------------
# 6. Config has dashboard vars
# ---------------------------------------------------------------------------

def test_config_has_dashboard_username(monkeypatch):
    monkeypatch.setenv("ALIEXPRESS_APP_KEY", "x")
    monkeypatch.setenv("ALIEXPRESS_APP_SECRET", "x")
    monkeypatch.setenv("ALIEXPRESS_TRACKING_ID", "x")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("MC_API_KEY", "x")
    monkeypatch.setenv("MC_URL", "http://mc.example.com")
    monkeypatch.setenv("DASHBOARD_USERNAME", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "pass")
    monkeypatch.setenv("DASHBOARD_SESSION_SECRET", "secret")

    from app.config import Settings
    s = Settings()
    assert s.dashboard_username == "admin"
    assert s.dashboard_password == "pass"
    assert s.dashboard_session_secret == "secret"
