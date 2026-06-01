"""Issue #141 — _scrape_with_scrapling: extração via JSON window._dida_config_._init_data_."""
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from app.scrapers.aliexpress import AliProduct, _find_product_list, _scrape_with_scrapling


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_product_item(
    product_id="111222333",
    display_title="USB Hub 4 Port",
    min_price=12.99,
    star_rating=4.7,
    trade_count=5000,
    img_url="//ae01.alicdn.com/kf/test.jpg",
) -> dict:
    return {
        "productId": product_id,
        "title": {"displayTitle": display_title},
        "prices": {
            "salePrice": {"minPrice": min_price, "currencyCode": "USD"},
        },
        "star_rating": str(star_rating),
        "real_trade_count": trade_count,
        "image": {"imgUrl": img_url},
    }


def _wrap_in_init_data(items: list) -> str:
    """Gera HTML com o JSON _init_data_ embutido."""
    data = {
        "data": {
            "data": {
                "root": {
                    "fields": {
                        "mods": {
                            "itemList": {
                                "content": items
                            }
                        }
                    }
                }
            }
        }
    }
    json_str = json.dumps(data)
    return f"<html><head></head><body><script>window._dida_config_._init_data_ = {json_str};</script></body></html>"


def _make_fetcher_page(html: str) -> MagicMock:
    page = MagicMock()
    page.content = html
    return page


def _mock_scrapling(fetcher_get_side_effect=None, fetcher_get_return_value=None):
    """Context manager que injeta scrapling mock em sys.modules."""
    mock_module = MagicMock()
    if fetcher_get_return_value is not None:
        mock_module.Fetcher.get.return_value = fetcher_get_return_value
    if fetcher_get_side_effect is not None:
        mock_module.Fetcher.get.side_effect = fetcher_get_side_effect
    return patch.dict(sys.modules, {"scrapling": mock_module})


# ── _find_product_list ───────────────────────────────────────────────────────

def test_find_product_list_finds_flat_list():
    """Lista com productId diretamente acessível."""
    items = [_make_product_item("1"), _make_product_item("2")]
    result = _find_product_list({"content": items})
    assert result == items


def test_find_product_list_finds_deeply_nested():
    """Busca recursiva em dicionários profundamente aninhados."""
    items = [_make_product_item("999")]
    deep = {"a": {"b": {"c": {"d": {"e": items}}}}}
    result = _find_product_list(deep)
    assert result == items


def test_find_product_list_returns_empty_when_no_product_id():
    """Retorna [] quando nenhuma lista contém productId."""
    data = {"foo": [{"bar": 1}, {"baz": 2}], "num": 42}
    result = _find_product_list(data)
    assert result == []


def test_find_product_list_handles_empty_dict():
    result = _find_product_list({})
    assert result == []


def test_find_product_list_handles_empty_list():
    result = _find_product_list([])
    assert result == []


def test_find_product_list_skips_list_without_product_id():
    """Lista de strings não é confundida com lista de produtos."""
    data = {"items": ["foo", "bar"], "products": [_make_product_item("42")]}
    result = _find_product_list(data)
    assert result[0]["productId"] == "42"


# ── _scrape_with_scrapling ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scrape_extracts_products_from_init_data():
    """Extrai produtos do JSON _init_data_ embutido no HTML."""
    items = [_make_product_item("111222333", "USB Hub 4 Port", 12.99, 4.7, 5000)]
    html = _wrap_in_init_data(items)
    page = _make_fetcher_page(html)

    with _mock_scrapling(fetcher_get_return_value=page):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    p = products[0]
    assert isinstance(p, AliProduct)
    assert p.product_id == "111222333"
    assert p.title == "USB Hub 4 Port"
    assert p.price_usd == 12.99
    assert p.rating == 4.7
    assert p.sale_count_30d == 5000
    assert p.image_url == "https://ae01.alicdn.com/kf/test.jpg"
    assert p.product_url == "https://www.aliexpress.com/item/111222333.html"
    assert p.category_id == "200003655"


@pytest.mark.asyncio
async def test_scrape_returns_empty_when_init_data_absent():
    """Retorna [] quando _init_data_ não está presente no HTML."""
    html = "<html><body><script>var x = 1;</script></body></html>"
    page = _make_fetcher_page(html)

    with _mock_scrapling(fetcher_get_return_value=page):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert products == []


@pytest.mark.asyncio
async def test_scrape_returns_empty_on_fetcher_exception():
    """Retorna [] quando Fetcher.get levanta exceção."""
    with _mock_scrapling(fetcher_get_side_effect=Exception("connection timeout")):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert products == []


@pytest.mark.asyncio
async def test_scrape_respects_max_results():
    """Respeita o limite max_results."""
    items = [_make_product_item(str(i), f"Product {i}") for i in range(20)]
    html = _wrap_in_init_data(items)
    page = _make_fetcher_page(html)

    with _mock_scrapling(fetcher_get_return_value=page):
        products = await _scrape_with_scrapling("200003655", max_results=5)

    assert len(products) == 5


@pytest.mark.asyncio
async def test_scrape_skips_items_without_product_id():
    """Itens sem productId são ignorados."""
    items = [
        {"title": {"displayTitle": "No ID"}, "prices": {"salePrice": {"minPrice": 1.0}}},
        _make_product_item("valid-id", "Valid Product"),
    ]
    html = _wrap_in_init_data(items)
    page = _make_fetcher_page(html)

    with _mock_scrapling(fetcher_get_return_value=page):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    assert products[0].product_id == "valid-id"


@pytest.mark.asyncio
async def test_scrape_skips_items_without_title():
    """Itens sem displayTitle são ignorados."""
    items = [
        {"productId": "no-title-id", "prices": {"salePrice": {"minPrice": 1.0}}},
        _make_product_item("has-title-id", "Has Title"),
    ]
    html = _wrap_in_init_data(items)
    page = _make_fetcher_page(html)

    with _mock_scrapling(fetcher_get_return_value=page):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    assert products[0].product_id == "has-title-id"


@pytest.mark.asyncio
async def test_scrape_does_not_use_css_selectors():
    """Confirma que page.css NÃO é chamado (sem CSS selectors)."""
    items = [_make_product_item("42")]
    html = _wrap_in_init_data(items)
    page = _make_fetcher_page(html)

    with _mock_scrapling(fetcher_get_return_value=page):
        await _scrape_with_scrapling("200003655", max_results=10)

    page.css.assert_not_called()


@pytest.mark.asyncio
async def test_scrape_uses_wholesale_url_for_keyword():
    """Com keyword, usa URL wholesale?SearchText=..."""
    import urllib.parse

    keyword = "USB hub"
    html = "<html><body></body></html>"
    page = _make_fetcher_page(html)
    captured = []

    mock_module = MagicMock()
    mock_module.Fetcher.get.side_effect = lambda url, **kw: captured.append(url) or page

    with patch.dict(sys.modules, {"scrapling": mock_module}):
        await _scrape_with_scrapling("200003655", max_results=10, keyword=keyword)

    assert len(captured) == 1
    assert urllib.parse.quote_plus(keyword) in captured[0]
    assert "wholesale" in captured[0]


@pytest.mark.asyncio
async def test_scrape_uses_category_url_without_keyword():
    """Sem keyword, usa URL /category/{id}/bestselling.html."""
    html = "<html><body></body></html>"
    page = _make_fetcher_page(html)
    captured = []

    mock_module = MagicMock()
    mock_module.Fetcher.get.side_effect = lambda url, **kw: captured.append(url) or page

    with patch.dict(sys.modules, {"scrapling": mock_module}):
        await _scrape_with_scrapling("200003655", max_results=10)

    assert len(captured) == 1
    assert "200003655" in captured[0]
    assert "bestselling" in captured[0]


@pytest.mark.asyncio
async def test_scrape_image_url_gets_https_prefix():
    """imgUrl sem protocolo (//ae01...) recebe prefixo https:."""
    items = [_make_product_item("1", img_url="//ae01.alicdn.com/kf/img.jpg")]
    html = _wrap_in_init_data(items)
    page = _make_fetcher_page(html)

    with _mock_scrapling(fetcher_get_return_value=page):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert products[0].image_url.startswith("https://")


@pytest.mark.asyncio
async def test_scrape_handles_missing_price_gracefully():
    """Preço ausente resulta em 0.0, sem exception."""
    item = {
        "productId": "456",
        "title": {"displayTitle": "No Price Product"},
        "prices": {},
        "star_rating": "4.0",
        "real_trade_count": 100,
        "image": {"imgUrl": "//ae01.alicdn.com/kf/img.jpg"},
    }
    html = _wrap_in_init_data([item])
    page = _make_fetcher_page(html)

    with _mock_scrapling(fetcher_get_return_value=page):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    assert products[0].price_usd == 0.0
