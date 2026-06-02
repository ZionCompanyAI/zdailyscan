"""Issue #159 — session cookies passados ao subprocess curl + delay entre targets no pipeline."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.aliexpress import _scrape_with_scrapling


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PRODUCT_ITEM = {
    "productId": "99159",
    "title": {"displayTitle": "Cookie Widget"},
    "prices": {"salePrice": {"minPrice": 9.99}},
    "star_rating": "4.8",
    "real_trade_count": "300",
    "image": {"imgUrl": "//ae01.alicdn.com/kf/cookie.jpg"},
}
_INIT_DATA = {"data": {"resultList": [_PRODUCT_ITEM]}}


def _make_curl_result(html: str, returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = html.encode("utf-8")
    return result


def _full_html() -> str:
    return (
        f"<html><script>window._dida_config_._init_data_ = {json.dumps(_INIT_DATA)};"
        "</script></html>"
    )


_COOKIES_JSON = json.dumps([
    {"name": "aep_usuc_f", "value": "site=us&c_tp=USD"},
    {"name": "xman_us_f", "value": "x_l=1&x_locale=en_US"},
    {"name": "empty_cookie", "value": ""},
])


# ---------------------------------------------------------------------------
# Fix 1 — Cookie header no curl quando env var está definida
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrapling_passes_cookie_header_when_env_set(monkeypatch):
    """Curl deve receber -H 'Cookie: ...' quando ALIEXPRESS_SESSION_COOKIES está definido."""
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", _COOKIES_JSON)
    curl_result = _make_curl_result(_full_html())

    with patch("subprocess.run", return_value=curl_result) as mock_sub:
        products = await _scrape_with_scrapling("200003655", max_results=10)

    cmd = mock_sub.call_args[0][0]
    assert "-H" in cmd
    cookie_idx = None
    for i, arg in enumerate(cmd):
        if arg == "-H" and i + 1 < len(cmd) and cmd[i + 1].startswith("Cookie:"):
            cookie_idx = i
            break
    assert cookie_idx is not None, "Cookie header não encontrado no comando curl"
    cookie_value = cmd[cookie_idx + 1]
    assert "aep_usuc_f=site=us&c_tp=USD" in cookie_value
    assert "xman_us_f=x_l=1&x_locale=en_US" in cookie_value
    # cookie vazio não deve aparecer
    assert "empty_cookie" not in cookie_value
    assert len(products) == 1


@pytest.mark.asyncio
async def test_scrapling_no_cookie_header_when_env_not_set(monkeypatch):
    """Curl NÃO deve incluir -H 'Cookie:' quando env var não está definida."""
    monkeypatch.delenv("ALIEXPRESS_SESSION_COOKIES", raising=False)
    curl_result = _make_curl_result(_full_html())

    with patch("subprocess.run", return_value=curl_result) as mock_sub:
        await _scrape_with_scrapling("200003655", max_results=10)

    cmd = mock_sub.call_args[0][0]
    for i, arg in enumerate(cmd):
        if arg == "-H" and i + 1 < len(cmd) and cmd[i + 1].lower().startswith("cookie:"):
            pytest.fail("Cookie header não deveria estar presente quando env var não está definida")


@pytest.mark.asyncio
async def test_scrapling_invalid_json_env_no_crash(monkeypatch):
    """JSON inválido em ALIEXPRESS_SESSION_COOKIES não deve causar crash — sem Cookie header."""
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", "isto nao eh json")
    curl_result = _make_curl_result(_full_html())

    with patch("subprocess.run", return_value=curl_result) as mock_sub:
        products = await _scrape_with_scrapling("200003655", max_results=10)

    cmd = mock_sub.call_args[0][0]
    for i, arg in enumerate(cmd):
        if arg == "-H" and i + 1 < len(cmd) and cmd[i + 1].lower().startswith("cookie:"):
            pytest.fail("Cookie header não deveria aparecer com JSON inválido")
    # deve retornar produtos normalmente (curl funcionou)
    assert isinstance(products, list)


@pytest.mark.asyncio
async def test_scrapling_empty_env_no_cookie_header(monkeypatch):
    """Env var vazia → sem Cookie header no curl."""
    monkeypatch.setenv("ALIEXPRESS_SESSION_COOKIES", "")
    curl_result = _make_curl_result(_full_html())

    with patch("subprocess.run", return_value=curl_result) as mock_sub:
        await _scrape_with_scrapling("200003655", max_results=10)

    cmd = mock_sub.call_args[0][0]
    for i, arg in enumerate(cmd):
        if arg == "-H" and i + 1 < len(cmd) and cmd[i + 1].lower().startswith("cookie:"):
            pytest.fail("Cookie header não deveria aparecer com env var vazia")


# ---------------------------------------------------------------------------
# Fix 2 — asyncio.sleep(2) entre targets no pipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_sleep_called_between_targets(monkeypatch):
    """run_daily_scan deve chamar asyncio.sleep(2) após cada target."""
    from app.analyzers.import_calculator import ImportCost
    from app.analyzers.mercado_livre import BRMarket
    from app.scrapers.models import AliProduct as ScraperProduct

    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1", "cat2"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: ["kw1"])

    def _market():
        return BRMarket(
            found=True, avg_price_brl=500.0, min_price_brl=300.0,
            max_price_brl=700.0, result_count=100, top_listings=[],
        )

    def _cost():
        return ImportCost(
            price_usd=10.0, freight_usd=5.0, tax_brl=25.0,
            total_cost_brl=100.0, regime="remessa_conforme",
        )

    def _products():
        return [ScraperProduct(
            product_id="p1", title="Test", price_usd=10.0, freight_usd=0.0,
            sale_count_30d=100, rating=4.5, image_url="//img.jpg",
            product_url="https://aliexpress.com/p1", category_id="cat1",
        )]

    sleep_calls = []

    async def fake_sleep(secs):
        sleep_calls.append(secs)

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=_products())),
        patch("app.pipeline.search_br_market", AsyncMock(return_value=_market())),
        patch("app.pipeline.calculate_import_cost", return_value=_cost()),
        patch("app.pipeline.asyncio") as mock_asyncio,
    ):
        mock_asyncio.sleep = fake_sleep
        from app.pipeline import run_daily_scan
        await run_daily_scan()

    # 3 targets (cat1, cat2, kw1) → 3 sleep(2) calls
    assert len(sleep_calls) == 3
    assert all(s == 2 for s in sleep_calls), f"Sleep values: {sleep_calls}"


@pytest.mark.asyncio
async def test_pipeline_sleep_value_is_2(monkeypatch):
    """O delay entre targets deve ser exatamente 2 segundos."""
    from app.analyzers.mercado_livre import BRMarket

    monkeypatch.setattr("app.pipeline.CATEGORIES", ["cat1"])
    monkeypatch.setattr("app.pipeline.get_active_keywords", lambda: [])

    sleep_calls = []

    async def fake_sleep(secs):
        sleep_calls.append(secs)

    with (
        patch("app.pipeline.get_hot_products", AsyncMock(return_value=[])),
        patch("app.pipeline.asyncio") as mock_asyncio,
    ):
        mock_asyncio.sleep = fake_sleep
        from app.pipeline import run_daily_scan
        await run_daily_scan()

    assert len(sleep_calls) == 1
    assert sleep_calls[0] == 2
