"""Issue #139 — SCRAPER_MODE=scrapling + fallback firecrawl→scrapling (httpx-based)."""
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.aliexpress import AliProduct, _scrape_with_scrapling, get_hot_products

_FAKE_PRODUCT = AliProduct(
    product_id="888",
    title="Scrapling Product",
    price_usd=5.99,
    sale_count_30d=0,
    rating=0.0,
    image_url="https://ae01.alicdn.com/kf/scrapling.jpg",
    product_url="https://www.aliexpress.com/item/888.html",
    category_id="200003655",
)

_PRODUCT_ITEM = {
    "productId": "888",
    "title": {"displayTitle": "Scrapling Product"},
    "prices": {"salePrice": {"minPrice": 5.99}},
    "star_rating": "0.0",
    "real_trade_count": "0",
    "image": {"imgUrl": "//ae01.alicdn.com/kf/scrapling.jpg"},
}

_INIT_DATA = {"data": {"resultList": [_PRODUCT_ITEM]}}


def _make_html(data: dict | None = None) -> str:
    if data is None:
        return "<html><script>window.foo = 1;</script></html>"
    return (
        f"<html><script>window._dida_config_._init_data_ = {json.dumps(data)};"
        "</script></html>"
    )


def _make_resp(html: str) -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.raise_for_status.return_value = None
    return resp


def _make_curl_result(html: str, returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = html.encode("utf-8")
    return result


def _make_mock_page(cards: list[dict] | None = None):
    """Mantido para compatibilidade — não é mais usado na implementação."""
    page = MagicMock()

    if cards is None:
        page.css.return_value = []
        return page

    mock_cards = []
    for card_data in cards:
        card = MagicMock()

        title_sel = MagicMock()
        title_sel.get.return_value = card_data.get("title", "")

        price_sel = MagicMock()
        price_sel.get.return_value = card_data.get("price", "0")

        url_sel = MagicMock()
        url_sel.get.return_value = card_data.get("href", "")

        img_sel = MagicMock()
        img_sel.get.return_value = card_data.get("image", "")

        def css_side_effect(selector, _card=card_data, _t=title_sel, _p=price_sel, _u=url_sel, _i=img_sel):
            if "item-title" in selector or "title" in selector:
                return _t
            if "price" in selector:
                return _p
            if "href" in selector:
                return _u
            if "img" in selector or "src" in selector:
                return _i
            return MagicMock(get=lambda default="": default)

        card.css.side_effect = css_side_effect
        mock_cards.append(card)

    page.css.return_value = mock_cards
    return page


@pytest.mark.asyncio
async def test_scrapling_mode_routes_to_scrape_with_scrapling():
    """SCRAPER_MODE=scrapling chama _scrape_with_scrapling."""
    with patch.dict(os.environ, {"SCRAPER_MODE": "scrapling"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_scrapling",
            new_callable=AsyncMock,
            return_value=[_FAKE_PRODUCT],
        ) as mock_scrapling:
            results = await get_hot_products("200003655")

    mock_scrapling.assert_called_once()
    assert results == [_FAKE_PRODUCT]


@pytest.mark.asyncio
async def test_scrapling_mode_does_not_call_firecrawl():
    """SCRAPER_MODE=scrapling não chama _scrape_with_firecrawl."""
    with patch.dict(os.environ, {"SCRAPER_MODE": "scrapling"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_scrapling",
            new_callable=AsyncMock,
            return_value=[_FAKE_PRODUCT],
        ):
            with patch(
                "app.scrapers.aliexpress._scrape_with_firecrawl",
                new_callable=AsyncMock,
            ) as mock_fc:
                await get_hot_products("200003655")

    mock_fc.assert_not_called()


@pytest.mark.asyncio
async def test_scrapling_returns_aliproducts_with_valid_fields():
    """_scrape_with_scrapling retorna lista de AliProduct com campos preenchidos."""
    with patch("subprocess.run", return_value=_make_curl_result(_make_html(_INIT_DATA))):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert isinstance(products, list)
    assert len(products) == 1
    assert all(isinstance(p, AliProduct) for p in products)
    assert all(p.category_id == "200003655" for p in products)


@pytest.mark.asyncio
async def test_scrapling_empty_page_returns_empty_list():
    """_scrape_with_scrapling retorna [] quando página não tem _init_data_."""
    with patch("asyncio.sleep"):
        with patch("subprocess.run", return_value=_make_curl_result(_make_html(None))):
            products = await _scrape_with_scrapling("200003655", max_results=10)

    assert products == []


@pytest.mark.asyncio
async def test_scrapling_exception_returns_empty_list():
    """_scrape_with_scrapling retorna [] quando subprocess.run levanta exceção."""
    with patch("asyncio.sleep"):
        with patch("subprocess.run", side_effect=Exception("network error")):
            products = await _scrape_with_scrapling("200003655", max_results=10)

    assert products == []


@pytest.mark.asyncio
async def test_firecrawl_402_falls_back_to_scrapling():
    """Firecrawl 402 Payment Required → fallback automático para scrapling."""
    with patch.dict(os.environ, {"SCRAPER_MODE": "firecrawl", "FIRECRAWL_API_KEY": "fc-test"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_firecrawl",
            new_callable=AsyncMock,
            side_effect=Exception("402 Payment Required"),
        ):
            with patch(
                "app.scrapers.aliexpress._scrape_with_scrapling",
                new_callable=AsyncMock,
                return_value=[_FAKE_PRODUCT],
            ) as mock_scrapling:
                results = await get_hot_products("200003655")

    mock_scrapling.assert_called_once()
    assert results == [_FAKE_PRODUCT]


@pytest.mark.asyncio
async def test_firecrawl_non_402_does_not_fallback_to_scrapling():
    """Firecrawl erro não-402 NÃO faz fallback para scrapling — retorna []."""
    with patch.dict(os.environ, {"SCRAPER_MODE": "firecrawl", "FIRECRAWL_API_KEY": "fc-test"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_firecrawl",
            new_callable=AsyncMock,
            side_effect=Exception("500 Internal Server Error"),
        ):
            with patch(
                "app.scrapers.aliexpress._scrape_with_scrapling",
                new_callable=AsyncMock,
                return_value=[_FAKE_PRODUCT],
            ) as mock_scrapling:
                results = await get_hot_products("200003655")

    mock_scrapling.assert_not_called()
    assert results == []


@pytest.mark.asyncio
async def test_scrapling_applies_min_rating_filter():
    """get_hot_products com scrapling aplica filtro min_rating."""
    low_rated = AliProduct(
        product_id="1",
        title="Low",
        price_usd=1.0,
        sale_count_30d=0,
        rating=2.0,
        image_url="",
        product_url="",
        category_id="200003655",
    )
    high_rated = AliProduct(
        product_id="2",
        title="High",
        price_usd=2.0,
        sale_count_30d=0,
        rating=4.8,
        image_url="",
        product_url="",
        category_id="200003655",
    )
    with patch.dict(os.environ, {"SCRAPER_MODE": "scrapling"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_scrapling",
            new_callable=AsyncMock,
            return_value=[low_rated, high_rated],
        ):
            results = await get_hot_products("200003655", min_rating=4.0)

    assert high_rated in results
    assert low_rated not in results


@pytest.mark.asyncio
async def test_scrapling_keyword_search_uses_wholesale_url():
    """_scrape_with_scrapling com keyword usa URL de busca (wholesale?SearchText=...)."""
    import urllib.parse

    keyword = "wireless earbuds"
    expected_url_fragment = urllib.parse.quote_plus(keyword)
    captured_urls = []

    def fake_run(cmd, **kwargs):
        captured_urls.append(cmd[-1])
        return _make_curl_result(_make_html(None))

    with patch("asyncio.sleep"):
        with patch("subprocess.run", side_effect=fake_run):
            await _scrape_with_scrapling("200003655", max_results=10, keyword=keyword)

    assert len(captured_urls) >= 1
    assert expected_url_fragment in captured_urls[0] or "wholesale" in captured_urls[0]
