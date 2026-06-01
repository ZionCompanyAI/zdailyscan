"""Tests for TASK-042: Settings — remover API AliExpress, categorias configuráveis, crawl4ai card."""

import os
from unittest.mock import AsyncMock, patch

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
# 1. Settings page — sem campos AliExpress API
# ---------------------------------------------------------------------------


def test_settings_no_aliexpress_api_card(monkeypatch):
    """Settings não deve ter card AliExpress API."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    body = resp.text
    assert "AliExpress API" not in body
    assert "app_key" not in body.lower()
    assert "app_secret" not in body.lower()


def test_settings_no_tracking_id_field(monkeypatch):
    """Settings não deve expor tracking_id como campo de configuração."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    # tracking_id não deve aparecer como chave visível no card de API AliExpress
    assert "Tracking ID" not in resp.text


# ---------------------------------------------------------------------------
# 2. Settings page — checkboxes de categorias
# ---------------------------------------------------------------------------


def test_settings_has_category_checkboxes(monkeypatch):
    """Settings deve ter checkboxes para as 3 categorias tech."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    body = resp.text
    # Deve conter os 3 IDs de categoria tech como checkboxes
    assert "200003655" in body
    assert "100003070" in body
    assert "200000783" in body
    assert "200000828" not in body
    assert "200000834" not in body
    assert 'type="checkbox"' in body


def test_settings_categories_form_posts_to_correct_url(monkeypatch):
    """Form de categorias deve POST para /dashboard/settings/categories."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "settings/categories" in resp.text


# ---------------------------------------------------------------------------
# 3. Settings page — card crawl4ai informativo
# ---------------------------------------------------------------------------


def test_settings_has_crawl4ai_card(monkeypatch):
    """Settings deve ter card informativo mostrando SCRAPER_MODE."""
    monkeypatch.setenv("SCRAPER_MODE", "crawl4ai")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    body = resp.text
    assert "crawl4ai" in body.lower() or "SCRAPER_MODE" in body or "scraper" in body.lower()


def test_settings_crawl4ai_shows_scraper_mode(monkeypatch):
    """Card crawl4ai deve exibir valor de SCRAPER_MODE."""
    monkeypatch.setenv("SCRAPER_MODE", "mock")
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.get("/dashboard/settings", cookies={"session": cookie})
    assert resp.status_code == 200
    assert "mock" in resp.text


# ---------------------------------------------------------------------------
# 4. POST /dashboard/settings/categories
# ---------------------------------------------------------------------------


def test_settings_categories_post_without_auth_redirects(monkeypatch):
    """POST /settings/categories sem auth redireciona para /login."""
    client = _make_client(monkeypatch)
    resp = client.post("/dashboard/settings/categories", data={"categories": ["200003655"]})
    assert resp.status_code in (302, 303, 307)
    assert "/login" in resp.headers["location"]


def test_settings_categories_post_redirects_to_settings(monkeypatch):
    """POST /settings/categories com auth redireciona para /dashboard/settings."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.post(
        "/dashboard/settings/categories",
        data={"categories": ["200003655", "100003070"]},
        cookies={"session": cookie},
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dashboard/settings"


def test_settings_categories_post_saves_to_env(monkeypatch):
    """POST /settings/categories salva SCAN_CATEGORIES em os.environ."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    # Limpar env antes
    monkeypatch.delenv("SCAN_CATEGORIES", raising=False)
    client.post(
        "/dashboard/settings/categories",
        data={"categories": ["200003655", "200000783"]},
        cookies={"session": cookie},
    )
    assert os.environ.get("SCAN_CATEGORIES") == "200003655,200000783"


def test_settings_categories_post_empty_list(monkeypatch):
    """POST /settings/categories sem categorias selecionadas salva string vazia."""
    client = _make_client(monkeypatch)
    cookie = _signed_cookie()
    resp = client.post(
        "/dashboard/settings/categories",
        data={},
        cookies={"session": cookie},
    )
    assert resp.status_code == 303
    saved = os.environ.get("SCAN_CATEGORIES", "UNSET")
    assert saved == "" or saved == "UNSET"


# ---------------------------------------------------------------------------
# 5. pipeline.get_active_categories()
# ---------------------------------------------------------------------------


def test_pipeline_get_active_categories_uses_env(monkeypatch):
    """get_active_categories() retorna IDs do env SCAN_CATEGORIES."""
    monkeypatch.setenv("SCAN_CATEGORIES", "200003655,100003070")
    from app.pipeline import get_active_categories

    result = get_active_categories()
    assert result == ["200003655", "100003070"]


def test_pipeline_get_active_categories_fallback(monkeypatch):
    """get_active_categories() retorna as 3 categorias tech padrão quando SCAN_CATEGORIES não definida."""
    monkeypatch.delenv("SCAN_CATEGORIES", raising=False)
    from app.pipeline import get_active_categories, CATEGORIES

    result = get_active_categories()
    assert result == CATEGORIES
    assert len(result) == 3


def test_pipeline_get_active_categories_ignores_invalid(monkeypatch):
    """get_active_categories() ignora IDs inválidos (não conhecidos)."""
    monkeypatch.setenv("SCAN_CATEGORIES", "200003655,INVALID_ID,100003070")
    from app.pipeline import get_active_categories

    result = get_active_categories()
    assert "INVALID_ID" not in result
    assert "200003655" in result
    assert "100003070" in result


def test_pipeline_get_active_categories_empty_env_falls_back(monkeypatch):
    """get_active_categories() com SCAN_CATEGORIES='' faz fallback para padrão."""
    monkeypatch.setenv("SCAN_CATEGORIES", "")
    from app.pipeline import get_active_categories, CATEGORIES

    result = get_active_categories()
    assert result == CATEGORIES


async def test_pipeline_run_uses_active_categories(monkeypatch):
    """run_daily_scan usa get_active_categories() — processa só categorias em SCAN_CATEGORIES."""
    monkeypatch.setenv("SCAN_CATEGORIES", "200003655")

    from app.analyzers.import_calculator import ImportCost
    from app.analyzers.mercado_livre import BRMarket
    from app.aliexpress import AliExpressProduct

    products = [AliExpressProduct(product_id="p1", title="Widget", price_usd=10.0)]
    market = BRMarket(
        found=True,
        avg_price_brl=500.0,
        min_price_brl=300.0,
        max_price_brl=700.0,
        result_count=200,
        top_listings=[],
    )
    cost = ImportCost(
        price_usd=10.0,
        freight_usd=5.0,
        tax_brl=25.65,
        total_cost_brl=100.0,
        regime="remessa_conforme",
    )

    calls = []

    async def mock_get_hot(cat_id, min_rating=0.0, max_results=100, keyword=""):
        if cat_id:
            calls.append(cat_id)
        return products

    with (
        patch("app.pipeline.get_hot_products", mock_get_hot),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=market)),
        patch("app.pipeline.calculate_import_cost", return_value=cost),
        patch("app.pipeline.send_daily_report", AsyncMock()),
        patch("app.pipeline.save_daily_report"),
    ):
        from app.pipeline import run_daily_scan

        await run_daily_scan()

    # Com SCAN_CATEGORIES=200003655 só 1 categoria deve ser processada
    assert calls == ["200003655"]
