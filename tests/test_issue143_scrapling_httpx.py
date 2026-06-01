"""Issue #143 — replace Scrapling Fetcher with httpx (no Playwright/camoufox in async context)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.scrapers.aliexpress import _find_product_list, _scrape_with_scrapling

_PRODUCT_ITEM = {
    "productId": "12345",
    "title": {"displayTitle": "Test Widget"},
    "prices": {"salePrice": {"minPrice": 12.5}},
    "star_rating": "4.5",
    "real_trade_count": "200",
    "image": {"imgUrl": "//ae01.alicdn.com/kf/test.jpg"},
}

_INIT_DATA = {"data": {"resultList": [_PRODUCT_ITEM]}}


def _make_html(data: dict | None = None) -> str:
    if data is None:
        return "<html><script>window.foo = 1;</script></html>"
    return (
        f"<html><script>window._dida_config_._init_data_ = {json.dumps(data)};"
        "</script></html>"
    )


def _make_resp(html: str, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.status_code = status_code
    resp.raise_for_status.return_value = None
    return resp


@pytest.mark.asyncio
async def test_scrapling_httpx_returns_products():
    """_scrape_with_scrapling extrai produtos de window._dida_config_._init_data_."""
    with patch("httpx.get", return_value=_make_resp(_make_html(_INIT_DATA))):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    p = products[0]
    assert p.product_id == "12345"
    assert p.title == "Test Widget"
    assert p.price_usd == 12.5
    assert p.rating == 4.5
    assert p.sale_count_30d == 200
    assert p.image_url == "https://ae01.alicdn.com/kf/test.jpg"
    assert p.category_id == "200003655"


@pytest.mark.asyncio
async def test_scrapling_no_init_data_returns_empty():
    """_scrape_with_scrapling retorna [] quando _init_data_ não está no HTML."""
    with patch("httpx.get", return_value=_make_resp(_make_html(None))):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert products == []


@pytest.mark.asyncio
async def test_scrapling_httpx_exception_returns_empty():
    """_scrape_with_scrapling retorna [] quando httpx.get levanta exceção."""
    with patch("httpx.get", side_effect=Exception("connection refused")):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert products == []


@pytest.mark.asyncio
async def test_scrapling_no_asyncio_to_thread():
    """_scrape_with_scrapling não usa asyncio.to_thread (sem Playwright)."""
    with patch("httpx.get", return_value=_make_resp(_make_html(None))):
        with patch("asyncio.to_thread") as mock_thread:
            await _scrape_with_scrapling("200003655", max_results=10)

    mock_thread.assert_not_called()


@pytest.mark.asyncio
async def test_scrapling_keyword_uses_wholesale_url():
    """Com keyword, _scrape_with_scrapling usa URL wholesale?SearchText=..."""
    import urllib.parse

    keyword = "wireless earbuds"
    captured = []

    def fake_get(url, **kwargs):
        captured.append(url)
        return _make_resp(_make_html(None))

    with patch("httpx.get", side_effect=fake_get):
        await _scrape_with_scrapling("200003655", max_results=10, keyword=keyword)

    assert len(captured) == 1
    assert urllib.parse.quote_plus(keyword) in captured[0]
    assert "wholesale" in captured[0]


@pytest.mark.asyncio
async def test_scrapling_no_keyword_uses_category_url():
    """Sem keyword, _scrape_with_scrapling usa URL de categoria/bestselling.html."""
    captured = []

    def fake_get(url, **kwargs):
        captured.append(url)
        return _make_resp(_make_html(None))

    with patch("httpx.get", side_effect=fake_get):
        await _scrape_with_scrapling("200003655", max_results=10)

    assert len(captured) == 1
    assert "200003655" in captured[0]
    assert "bestselling" in captured[0]


@pytest.mark.asyncio
async def test_scrapling_max_results_respected():
    """_scrape_with_scrapling respeita max_results."""
    items = [
        {**_PRODUCT_ITEM, "productId": str(i), "title": {"displayTitle": f"P{i}"}}
        for i in range(5)
    ]
    data = {"data": {"resultList": items}}
    with patch("httpx.get", return_value=_make_resp(_make_html(data))):
        products = await _scrape_with_scrapling("200003655", max_results=3)

    assert len(products) == 3


@pytest.mark.asyncio
async def test_scrapling_image_protocol_added():
    """URL de imagem protocol-relative '//' recebe 'https:' no prefixo."""
    with patch("httpx.get", return_value=_make_resp(_make_html(_INIT_DATA))):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert products[0].image_url.startswith("https://")


def test_find_product_list_finds_nested_list():
    """_find_product_list encontra lista de produtos aninhada em dict arbitrário."""
    products = [{"productId": "1"}, {"productId": "2"}]
    data = {"data": {"resultList": products}}
    assert _find_product_list(data) == products


def test_find_product_list_returns_none_when_absent():
    """_find_product_list retorna None quando não há lista com productId."""
    assert _find_product_list({"foo": "bar", "baz": [1, 2, 3]}) is None


def test_find_product_list_handles_deep_nesting():
    """_find_product_list lida com aninhamento profundo."""
    products = [{"productId": "99"}]
    data = {"a": {"b": {"c": {"d": products}}}}
    assert _find_product_list(data) == products
