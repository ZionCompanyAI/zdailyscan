"""RED tests — issue #126: substituir crawl4ai por httpx JSON API."""
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.aliexpress import get_hot_products
from app.scrapers.models import AliProduct

# ── helpers ────────────────────────────────────────────────────────────────────

_MOCK_JSON_BODY = json.dumps({
    "data": {
        "result": {
            "resultList": [
                {
                    "item": {
                        "itemId": "1005001",
                        "title": "Wireless Earbuds Pro",
                        "prices": {
                            "salePrice": {"formattedPrice": "US $12.99"}
                        },
                        "tradeDesc": "2500+ sold",
                        "averageStar": "4.7",
                        "imageUrl": "//ae01.alicdn.com/kf/earbuds.jpg",
                    }
                },
                {
                    "item": {
                        "itemId": "1005002",
                        "title": "LED Strip Lights",
                        "prices": {
                            "salePrice": {"formattedPrice": "US $5.49"}
                        },
                        "tradeDesc": "8000+ sold",
                        "averageStar": "4.5",
                        "imageUrl": "//ae01.alicdn.com/kf/strip.jpg",
                    }
                },
            ]
        }
    }
})

_HTML_BODY = "<!DOCTYPE html><html><head><title>AliExpress</title></head><body>bot-check</body></html>"


def _mock_response(body: str, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.text = body
    resp.status_code = status_code
    return resp


def _mock_httpx_client(*responses: str):
    """Returns a context-manager mock for httpx.AsyncClient returning responses in order."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=[_mock_response(r) for r in responses])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ── tests ──────────────────────────────────────────────────────────────────────


async def test_default_scraper_mode_is_http():
    """Sem SCRAPER_MODE definido, o default deve ser 'http' (não crawl4ai)."""
    env = {k: v for k, v in os.environ.items() if k != "SCRAPER_MODE"}
    with patch.dict(os.environ, env, clear=True):
        with patch(
            "app.scrapers.aliexpress._scrape_with_http",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_http:
            with patch(
                "app.scrapers.aliexpress._scrape_with_crawl4ai",
                new_callable=AsyncMock,
                return_value=[],
            ) as mock_crawl:
                await get_hot_products("200003655")

    mock_http.assert_called_once(), "SCRAPER_MODE default deve chamar _scrape_with_http"
    # crawl4ai pode ser chamado como fallback se http retornar []
    # mas _scrape_with_http deve ser chamado primeiro
    http_call_index = mock_http.call_args_list[0] if mock_http.called else None
    assert http_call_index is not None


async def test_http_mode_calls_scrape_with_http():
    """SCRAPER_MODE=http deve chamar _scrape_with_http."""
    with patch.dict(os.environ, {"SCRAPER_MODE": "http"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_http",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_http:
            with patch(
                "app.scrapers.aliexpress._scrape_with_crawl4ai",
                new_callable=AsyncMock,
                return_value=[],
            ):
                await get_hot_products("200003655")

    mock_http.assert_called_once()


async def test_crawl4ai_mode_still_uses_crawl4ai():
    """SCRAPER_MODE=crawl4ai deve chamar _scrape_with_crawl4ai, não _scrape_with_http."""
    with patch.dict(os.environ, {"SCRAPER_MODE": "crawl4ai"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_http",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_http:
            with patch(
                "app.scrapers.aliexpress._scrape_with_crawl4ai",
                new_callable=AsyncMock,
                return_value=[],
            ) as mock_crawl:
                await get_hot_products("200003655")

    mock_http.assert_not_called()
    mock_crawl.assert_called_once()


async def test_http_parses_valid_json_response():
    """_scrape_with_http deve parsear JSON válido e retornar AliProduct list."""
    client_mock = _mock_httpx_client(_MOCK_JSON_BODY)
    with patch("httpx.AsyncClient", return_value=client_mock):
        from app.scrapers.aliexpress import _scrape_with_http
        results = await _scrape_with_http("200003655", 100)

    assert len(results) == 2
    assert all(isinstance(p, AliProduct) for p in results)
    assert results[0].product_id == "1005001"
    assert results[0].title == "Wireless Earbuds Pro"
    assert results[0].price_usd == pytest.approx(12.99)
    assert results[0].sale_count_30d == 2500
    assert results[0].rating == pytest.approx(4.7)
    assert results[0].image_url.startswith("https://")
    assert results[0].product_url == "https://www.aliexpress.com/item/1005001.html"
    assert results[0].category_id == "200003655"


async def test_http_returns_empty_on_html_response():
    """Resposta HTML (bot-check) deve retornar [] e não levantar exceção."""
    # Desktop returns HTML, mobile also returns HTML
    client_mock = _mock_httpx_client(_HTML_BODY, _HTML_BODY)
    with patch("httpx.AsyncClient", return_value=client_mock):
        from app.scrapers.aliexpress import _scrape_with_http
        results = await _scrape_with_http("200003655", 100)

    assert results == []


async def test_http_tries_mobile_after_desktop_empty():
    """Desktop URL bloqueia (HTML) → tenta URL mobile como fallback."""
    client_mock = _mock_httpx_client(_HTML_BODY, _MOCK_JSON_BODY)
    with patch("httpx.AsyncClient", return_value=client_mock):
        from app.scrapers.aliexpress import _scrape_with_http
        results = await _scrape_with_http("200003655", 100)

    # Mobile should have returned products
    assert len(results) == 2
    # httpx.AsyncClient.get must have been called twice (desktop + mobile)
    assert client_mock.get.call_count == 2


async def test_http_request_has_required_headers():
    """Request deve incluir User-Agent Chrome, Accept json, Referer e X-Requested-With."""
    client_mock = _mock_httpx_client(_MOCK_JSON_BODY)
    with patch("httpx.AsyncClient", return_value=client_mock):
        from app.scrapers.aliexpress import _scrape_with_http
        await _scrape_with_http("200003655", 100)

    call_kwargs = client_mock.get.call_args
    headers = call_kwargs.kwargs.get("headers", call_kwargs.args[1] if len(call_kwargs.args) > 1 else {})
    assert "User-Agent" in headers or "user-agent" in {k.lower() for k in headers}
    assert "Chrome" in str(headers.get("User-Agent", headers.get("user-agent", "")))
    assert "Accept" in headers
    assert "application/json" in headers["Accept"]
    assert "Referer" in headers or "referer" in {k.lower() for k in headers}
    assert "X-Requested-With" in headers


async def test_http_includes_cookies_in_request():
    """Com ALIEXPRESS_SESSION_COOKIES setado, cookies devem ser passados ao AsyncClient."""
    cookies_env = json.dumps([{"name": "aep_usuc_f", "value": "abc123"}])
    client_mock = _mock_httpx_client(_MOCK_JSON_BODY)
    with patch("httpx.AsyncClient", return_value=client_mock) as mock_class:
        from app.scrapers.aliexpress import _scrape_with_http
        await _scrape_with_http("200003655", 100, session_cookies=cookies_env)

    # cookies passed to AsyncClient constructor (not per-request) to avoid deprecation
    call_kwargs = mock_class.call_args
    cookies = call_kwargs.kwargs.get("cookies", {})
    assert "aep_usuc_f" in cookies
    assert cookies["aep_usuc_f"] == "abc123"


async def test_http_handles_network_exception_gracefully():
    """Exceção de rede deve retornar [] sem propagar."""
    client_mock = MagicMock()
    client_mock.get = AsyncMock(side_effect=Exception("connection refused"))
    client_mock.__aenter__ = AsyncMock(return_value=client_mock)
    client_mock.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=client_mock):
        from app.scrapers.aliexpress import _scrape_with_http
        results = await _scrape_with_http("200003655", 100)

    assert results == []


async def test_http_max_results_respected():
    """Retornar no máximo max_results produtos."""
    client_mock = _mock_httpx_client(_MOCK_JSON_BODY)
    with patch("httpx.AsyncClient", return_value=client_mock):
        from app.scrapers.aliexpress import _scrape_with_http
        results = await _scrape_with_http("200003655", max_results=1)

    assert len(results) == 1


async def test_parse_fn_json_image_url_adds_https():
    """imageUrl com '//' deve ser prefixado com 'https:'."""
    from app.scrapers.aliexpress import _parse_fn_json

    data = {
        "data": {
            "result": {
                "resultList": [
                    {
                        "item": {
                            "itemId": "999",
                            "title": "Test",
                            "prices": {"salePrice": {"formattedPrice": "US $1.00"}},
                            "tradeDesc": "100 sold",
                            "averageStar": "4.5",
                            "imageUrl": "//ae01.alicdn.com/img.jpg",
                        }
                    }
                ]
            }
        }
    }
    results = _parse_fn_json(data, "200003655", 10)
    assert results[0].image_url == "https://ae01.alicdn.com/img.jpg"


async def test_http_mode_fallback_to_crawl4ai_when_empty():
    """Modo http com HTTP retornando [] deve fazer fallback para crawl4ai."""
    _crawl_product = AliProduct(
        product_id="crawl126",
        title="Crawl Fallback",
        price_usd=5.0,
        sale_count_30d=100,
        rating=4.5,
        image_url="https://ae01.alicdn.com/fallback.jpg",
        product_url="https://www.aliexpress.com/item/crawl126.html",
        category_id="200003655",
    )
    with patch.dict(os.environ, {"SCRAPER_MODE": "http"}):
        with patch(
            "app.scrapers.aliexpress._scrape_with_http",
            new_callable=AsyncMock,
            return_value=[],
        ):
            with patch(
                "app.scrapers.aliexpress._scrape_with_crawl4ai",
                new_callable=AsyncMock,
                return_value=[_crawl_product],
            ) as mock_crawl:
                results = await get_hot_products("200003655")

    mock_crawl.assert_called_once()
    assert results == [_crawl_product]
