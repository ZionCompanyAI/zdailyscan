"""Tests for issue #76: scanner page respects active categories from Settings."""

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


def test_scanner_only_active_category_is_checked(monkeypatch, tmp_path):
    """When SCAN_CATEGORIES has only one ID, only that category checkbox is checked."""
    import app.storage as storage_module

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SCAN_CATEGORIES", "200003655")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scanner", cookies={"session": cookie})
    assert resp.status_code == 200
    body = resp.text

    # The active category checkbox must be pre-checked
    assert 'value="200003655" checked' in body or 'value="200003655"  checked' in body

    # Inactive categories must NOT be checked
    for inactive_id in ["100003070", "200000783", "200000828", "200000834"]:
        # The inactive id appears in the form but without checked attribute adjacent to it
        assert f'value="{inactive_id}" checked' not in body


def test_scanner_all_checked_when_no_scan_categories_set(monkeypatch, tmp_path):
    """When SCAN_CATEGORIES is unset (default), all categories are active and checked."""
    import app.storage as storage_module

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("SCAN_CATEGORIES", raising=False)
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scanner", cookies={"session": cookie})
    assert resp.status_code == 200
    body = resp.text

    for cat_id in ["200003655", "100003070", "200000783", "200000828", "200000834"]:
        assert f'value="{cat_id}" checked' in body or f'value="{cat_id}"  checked' in body


def test_scanner_empty_scan_categories_falls_back_to_all_checked(monkeypatch, tmp_path):
    """When SCAN_CATEGORIES is empty string, get_active_categories falls back to all defaults."""
    import app.storage as storage_module

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SCAN_CATEGORIES", "")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scanner", cookies={"session": cookie})
    assert resp.status_code == 200
    body = resp.text

    for cat_id in ["200003655", "100003070", "200000783", "200000828", "200000834"]:
        assert f'value="{cat_id}" checked' in body or f'value="{cat_id}"  checked' in body
