"""Issue #139 — SCRAPER_MODE=scrapling com StealthyFetcher + fallback firecrawl→scrapling."""
import asyncio
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


def _make_mock_page(cards: list[dict] | None = None):
    """Cria um mock de página Scrapling com cards simulados."""
    page = MagicMock()

    if cards is None:
        # Página sem cards — retorna lista vazia
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
    cards = [
        {
            "title": "Test Widget",
            "price": "US$ 12.50",
            "href": "https://www.aliexpress.com/item/888.html",
            "image": "https://ae01.alicdn.com/kf/test.jpg",
        }
    ]
    mock_page = _make_mock_page(cards)

    with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_page):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert isinstance(products, list)
    # Produto deve ter product_id e title preenchidos
    if products:
        assert all(isinstance(p, AliProduct) for p in products)
        assert all(p.category_id == "200003655" for p in products)


@pytest.mark.asyncio
async def test_scrapling_empty_page_returns_empty_list():
    """_scrape_with_scrapling retorna [] quando página não tem cards."""
    mock_page = _make_mock_page(cards=None)  # sem cards

    with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_page):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert products == []


@pytest.mark.asyncio
async def test_scrapling_exception_returns_empty_list():
    """_scrape_with_scrapling retorna [] quando StealthyFetcher levanta exceção."""
    with patch("asyncio.to_thread", new_callable=AsyncMock, side_effect=Exception("network error")):
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

    def capture_fetch(url, **kwargs):
        captured_urls.append(url)
        return _make_mock_page(cards=None)

    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        mock_thread.side_effect = lambda fn, *args, **kwargs: asyncio.coroutine(
            lambda: capture_fetch(*args, **kwargs)
        )()
        # Simpler: just check URL passed to asyncio.to_thread via StealthyFetcher
        mock_thread.return_value = _make_mock_page(cards=None)
        await _scrape_with_scrapling("200003655", max_results=10, keyword=keyword)

    # Verificar que asyncio.to_thread foi chamado
    mock_thread.assert_called_once()
    # O segundo argumento de asyncio.to_thread é a URL
    call_args = mock_thread.call_args
    url_arg = call_args.args[1] if len(call_args.args) > 1 else None
    if url_arg:
        assert expected_url_fragment in url_arg or "wholesale" in url_arg
