"""Tests for TASK-036: Explorer, Scanner, Settings — Fase 1 UI Dashboard."""

import json
import os
from unittest.mock import AsyncMock, patch

# Env vars must be set before any app import
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


def _minimal_scan(date: str = "2026-01-15", product_id: str = "p1") -> dict:
    return {
        "scan_id": "abc123",
        "date": date,
        "products": [
            {
                "product_id": product_id,
                "title": "Test Widget",
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


# ---------------------------------------------------------------------------
# 1. Explorer page
# ---------------------------------------------------------------------------

def test_explorer_without_auth_redirects(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/dashboard/explorer")
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_explorer_with_auth_returns_200(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/explorer", cookies={"session": cookie})
    assert resp.status_code == 200


def test_explorer_no_bootstrap(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/explorer", cookies={"session": cookie})
    assert b"bootstrap" not in resp.content.lower()


def test_explorer_has_oklch_tokens(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/explorer", cookies={"session": cookie})
    body = resp.text
    assert "oklch" in body or "var(--color-" in body


def test_explorer_renders_products(monkeypatch, tmp_path):
    import app.storage as storage_module
    scans_dir = tmp_path / "scans"
    scans_dir.mkdir()
    monkeypatch.setattr(storage_module, "SCANS_DIR", scans_dir)
    (scans_dir / "2026-01-15.json").write_text(json.dumps(_minimal_scan()))
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/explorer", cookies={"session": cookie})
    assert resp.status_code == 200
    assert b"Test Widget" in resp.content


# ---------------------------------------------------------------------------
# 2. Scanner page
# ---------------------------------------------------------------------------

def test_scanner_without_auth_redirects(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/dashboard/scanner")
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_scanner_with_auth_returns_200(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scanner", cookies={"session": cookie})
    assert resp.status_code == 200


def test_scanner_no_bootstrap(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scanner", cookies={"session": cookie})
    assert b"bootstrap" not in resp.content.lower()


def test_scanner_shows_history(monkeypatch, tmp_path):
    import app.storage as storage_module
    scans_dir = tmp_path / "scans"
    scans_dir.mkdir()
    monkeypatch.setattr(storage_module, "SCANS_DIR", scans_dir)
    (scans_dir / "2026-01-15.json").write_text(json.dumps(_minimal_scan()))
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scanner", cookies={"session": cookie})
    assert b"2026-01-15" in resp.content


# ---------------------------------------------------------------------------
# 3. Settings page
# ---------------------------------------------------------------------------

def test_settings_without_auth_redirects(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/dashboard/settings")
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_settings_with_auth_returns_200(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200


def test_settings_no_bootstrap(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert b"bootstrap" not in resp.content.lower()


def test_settings_masks_sensitive_fields(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    # Should not expose full secret values
    assert b"ALIEXPRESS_APP_SECRET" not in resp.content
    assert b"***" in resp.content or b"mask" in resp.content.lower()


# ---------------------------------------------------------------------------
# 4. JSON API — /dashboard/products
# ---------------------------------------------------------------------------

def test_products_api_without_auth_redirects(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/dashboard/products")
    assert resp.status_code in (302, 303, 307)


def test_products_api_returns_json_list(monkeypatch, tmp_path):
    import app.storage as storage_module
    scans_dir = tmp_path / "scans"
    scans_dir.mkdir()
    monkeypatch.setattr(storage_module, "SCANS_DIR", scans_dir)
    (scans_dir / "2026-01-15.json").write_text(json.dumps(_minimal_scan()))
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/products", cookies={"session": cookie})
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert isinstance(data["products"], list)
    assert len(data["products"]) == 1
    assert data["products"][0]["product_id"] == "p1"


def test_products_api_deduplicates_by_product_id(monkeypatch, tmp_path):
    import app.storage as storage_module
    scans_dir = tmp_path / "scans"
    scans_dir.mkdir()
    monkeypatch.setattr(storage_module, "SCANS_DIR", scans_dir)
    # Same product_id in two scan files — should appear only once
    (scans_dir / "2026-01-15.json").write_text(json.dumps(_minimal_scan("2026-01-15", "p1")))
    (scans_dir / "2026-01-16.json").write_text(json.dumps(_minimal_scan("2026-01-16", "p1")))
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/products", cookies={"session": cookie})
    data = resp.json()
    assert len(data["products"]) == 1


def test_products_api_min_score_filter(monkeypatch, tmp_path):
    import app.storage as storage_module
    scans_dir = tmp_path / "scans"
    scans_dir.mkdir()
    monkeypatch.setattr(storage_module, "SCANS_DIR", scans_dir)
    (scans_dir / "2026-01-15.json").write_text(json.dumps(_minimal_scan()))
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    # score_total=0.75 → 75 as percentage; filter min_score=80 should exclude it
    resp = client.get("/dashboard/products?min_score=80", cookies={"session": cookie})
    data = resp.json()
    assert len(data["products"]) == 0


def test_products_api_empty_when_no_scans(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/products", cookies={"session": cookie})
    assert resp.status_code == 200
    assert resp.json()["products"] == []


# ---------------------------------------------------------------------------
# 5. JSON API — /dashboard/scans
# ---------------------------------------------------------------------------

def test_scans_api_returns_json_list(monkeypatch, tmp_path):
    import app.storage as storage_module
    scans_dir = tmp_path / "scans"
    scans_dir.mkdir()
    monkeypatch.setattr(storage_module, "SCANS_DIR", scans_dir)
    (scans_dir / "2026-01-15.json").write_text(json.dumps(_minimal_scan()))
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scans", cookies={"session": cookie})
    assert resp.status_code == 200
    data = resp.json()
    assert "scans" in data
    assert len(data["scans"]) == 1
    s = data["scans"][0]
    assert s["scan_id"] == "abc123"
    assert s["date"] == "2026-01-15"
    assert s["product_count"] == 1
    assert s["status"] == "completed"


def test_scans_api_empty_when_no_scans(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scans", cookies={"session": cookie})
    assert resp.status_code == 200
    assert resp.json()["scans"] == []


# ---------------------------------------------------------------------------
# 6. POST /dashboard/scan/trigger
# ---------------------------------------------------------------------------

def test_scan_trigger_without_auth_redirects(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.post("/dashboard/scan/trigger")
    assert resp.status_code in (302, 303, 307)


def test_scan_trigger_returns_started(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    with patch("app.routers.dashboard.run_daily_scan", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = None
        resp = client.post("/dashboard/scan/trigger", cookies={"session": cookie})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "started"
    assert "scan_id" in data
    assert len(data["scan_id"]) > 0


# ---------------------------------------------------------------------------
# 7. GET /dashboard/scan/{scan_id}/status
# ---------------------------------------------------------------------------

def test_scan_status_unknown_returns_not_found(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scan/nonexistent-id/status", cookies={"session": cookie})
    assert resp.status_code == 404


def test_scan_status_returns_running_after_trigger(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    with patch("app.routers.dashboard.run_daily_scan", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = None
        trigger_resp = client.post("/dashboard/scan/trigger", cookies={"session": cookie})
    scan_id = trigger_resp.json()["scan_id"]
    status_resp = client.get(f"/dashboard/scan/{scan_id}/status", cookies={"session": cookie})
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["scan_id"] == scan_id
    assert data["status"] in ("running", "completed", "failed")


# ---------------------------------------------------------------------------
# 8. POST /dashboard/settings/telegram-test
# ---------------------------------------------------------------------------

def test_telegram_test_without_auth_redirects(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.post("/dashboard/settings/telegram-test")
    assert resp.status_code in (302, 303, 307)


def test_telegram_test_with_auth_returns_json(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    with patch("httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = AsyncMock()
        mock_resp.raise_for_status = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client
        resp = client.post("/dashboard/settings/telegram-test", cookies={"session": cookie})
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
