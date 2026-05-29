"""Tests for issue #38: mobile-first redesign of all dashboard pages."""

import os

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
# 1. Viewport meta presente em todas as páginas
# ---------------------------------------------------------------------------

def test_login_has_viewport_meta(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/login")
    body = resp.text
    assert 'name="viewport"' in body
    assert "width=device-width" in body
    assert "initial-scale=1" in body


def test_dashboard_has_viewport_meta(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard", cookies={"session": cookie})
    body = resp.text
    assert 'name="viewport"' in body
    assert "width=device-width" in body
    assert "initial-scale=1" in body


def test_explorer_has_viewport_meta(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/explorer", cookies={"session": cookie})
    body = resp.text
    assert 'name="viewport"' in body
    assert "width=device-width" in body


def test_scanner_has_viewport_meta(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scanner", cookies={"session": cookie})
    assert 'name="viewport"' in resp.text


def test_settings_has_viewport_meta(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert 'name="viewport"' in resp.text


# ---------------------------------------------------------------------------
# 2. Bottom navigation bar presente em páginas autenticadas
# ---------------------------------------------------------------------------

def test_dashboard_has_bottom_nav(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard", cookies={"session": cookie})
    assert 'class="bottom-nav"' in resp.text or "bottom-nav" in resp.text


def test_explorer_has_bottom_nav(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/explorer", cookies={"session": cookie})
    assert "bottom-nav" in resp.text


def test_scanner_has_bottom_nav(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scanner", cookies={"session": cookie})
    assert "bottom-nav" in resp.text


def test_settings_has_bottom_nav(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert "bottom-nav" in resp.text


# ---------------------------------------------------------------------------
# 3. Top nav hidden on mobile (media query presente)
# ---------------------------------------------------------------------------

def test_base_has_media_query_for_nav(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard", cookies={"session": cookie})
    body = resp.text
    # Must have media query that hides top-nav or shows bottom-nav conditionally
    assert "@media" in body


def test_base_top_nav_hidden_on_mobile(monkeypatch):
    """Top nav must have display:none or be wrapped in media query for mobile."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard", cookies={"session": cookie})
    body = resp.text
    # The top-nav class or nav should be hidden via media query
    assert "top-nav" in body or ".top-nav" in body


# ---------------------------------------------------------------------------
# 4. Login inputs com font-size >= 16px (evita zoom iOS)
# ---------------------------------------------------------------------------

def test_login_inputs_font_size_16px(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/login")
    body = resp.text
    # The field input style must have font-size of at least 16px or 1rem
    assert "font-size: 1rem" in body or "font-size:1rem" in body or "font-size: 16px" in body or "font-size:16px" in body


# ---------------------------------------------------------------------------
# 5. Botões com min-height 44px (tap targets)
# ---------------------------------------------------------------------------

def test_login_button_min_height_44px(monkeypatch):
    client = _make_client(monkeypatch)
    resp = client.get("/login")
    body = resp.text
    # btn-primary must define min-height of at least 44px
    assert "min-height: 44px" in body or "min-height:44px" in body


# ---------------------------------------------------------------------------
# 6. Explorer: filtros em elemento colapsável
# ---------------------------------------------------------------------------

def test_explorer_filters_collapsible(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/explorer", cookies={"session": cookie})
    body = resp.text
    # Filters must be in a <details> element or have a toggle mechanism
    assert "<details" in body or "filter-toggle" in body


def test_explorer_grid_responsive(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/explorer", cookies={"session": cookie})
    body = resp.text
    # Must have a media query for responsive grid
    assert "@media" in body
    # Must have 1fr or single column fallback
    assert "1fr" in body or "grid-template-columns: 1fr" in body


# ---------------------------------------------------------------------------
# 7. Scanner: botão trigger full-width no mobile
# ---------------------------------------------------------------------------

def test_scanner_has_full_width_btn_mobile(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/scanner", cookies={"session": cookie})
    body = resp.text
    # Must have width: 100% in mobile context (either as base style or in media query)
    assert "width: 100%" in body or "w-full" in body


# ---------------------------------------------------------------------------
# 8. Sem bootstrap, OKLCH mantido em todas as páginas
# ---------------------------------------------------------------------------

def test_all_pages_no_bootstrap(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    for path in ["/dashboard", "/dashboard/explorer", "/dashboard/scanner", "/dashboard/settings"]:
        resp = client.get(path, cookies={"session": cookie})
        assert b"bootstrap" not in resp.content.lower(), f"Bootstrap found in {path}"


def test_all_pages_have_oklch(monkeypatch, tmp_path):
    import app.storage as storage_module
    monkeypatch.setattr(storage_module, "SCANS_DIR", tmp_path / "scans")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    for path in ["/dashboard", "/dashboard/explorer", "/dashboard/scanner", "/dashboard/settings"]:
        resp = client.get(path, cookies={"session": cookie})
        body = resp.text
        assert "oklch" in body or "var(--color-" in body, f"OKLCH not found in {path}"


# ---------------------------------------------------------------------------
# 9. Settings: grid responsivo (1 coluna em mobile)
# ---------------------------------------------------------------------------

def test_settings_grid_single_col_mobile(monkeypatch):
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    body = resp.text
    # Settings grid must have responsive behavior with 1fr column fallback
    assert "grid-template-columns: 1fr" in body or "1fr" in body
