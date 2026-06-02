"""Issue #150 — Accept-Encoding headers + retry 3x em _scrape_with_scrapling."""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.scrapers.aliexpress import _SCRAPLING_HEADERS, _scrape_with_scrapling

_PRODUCT_ITEM = {
    "productId": "54321",
    "title": {"displayTitle": "Retry Widget"},
    "prices": {"salePrice": {"minPrice": 8.0}},
    "star_rating": "4.2",
    "real_trade_count": "300",
    "image": {"imgUrl": "//ae01.alicdn.com/kf/retry.jpg"},
}

_INIT_DATA = {"data": {"resultList": [_PRODUCT_ITEM]}}


def _thin_html() -> str:
    return "<html><body>Loading...</body></html>"


def _full_html(data: dict | None = None) -> str:
    if data is None:
        data = _INIT_DATA
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


def _make_curl_result(html: str, returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = html.encode("utf-8")
    return result


# --- Header presence tests ---


def test_scrapling_headers_contain_accept_encoding():
    """_SCRAPLING_HEADERS deve conter Accept-Encoding: gzip, deflate, br."""
    assert "Accept-Encoding" in _SCRAPLING_HEADERS
    assert "gzip" in _SCRAPLING_HEADERS["Accept-Encoding"]


def test_scrapling_headers_contain_connection():
    """_SCRAPLING_HEADERS deve conter Connection."""
    assert "Connection" in _SCRAPLING_HEADERS


def test_scrapling_headers_contain_sec_fetch_dest():
    """_SCRAPLING_HEADERS deve conter Sec-Fetch-Dest."""
    assert "Sec-Fetch-Dest" in _SCRAPLING_HEADERS


# --- Retry behavior tests ---


@pytest.mark.asyncio
async def test_scrapling_no_retry_on_first_success():
    """subprocess.run é chamado apenas 1x quando a primeira resposta já tem JS data."""
    with patch("asyncio.sleep") as mock_sleep:
        with patch("subprocess.run", return_value=_make_curl_result(_full_html())) as mock_sub:
            products = await _scrape_with_scrapling("200003655", max_results=10)

    mock_sub.assert_called_once()
    mock_sleep.assert_not_called()
    assert len(products) == 1


@pytest.mark.asyncio
async def test_scrapling_retry_on_thin_page_succeeds_on_second_attempt():
    """Thin page na 1ª tentativa → retry → JS data na 2ª → retorna produtos."""
    responses = [_make_curl_result(_thin_html()), _make_curl_result(_full_html())]

    with patch("asyncio.sleep") as mock_sleep:
        with patch("subprocess.run", side_effect=responses) as mock_sub:
            products = await _scrape_with_scrapling("200003655", max_results=10)

    assert mock_sub.call_count == 2
    mock_sleep.assert_called_once_with(4)
    assert len(products) == 1
    assert products[0].product_id == "54321"


@pytest.mark.asyncio
async def test_scrapling_retry_exhausted_returns_empty():
    """Após 3 tentativas sem JS data, retorna []."""
    with patch("asyncio.sleep") as mock_sleep:
        with patch("subprocess.run", return_value=_make_curl_result(_thin_html())) as mock_sub:
            products = await _scrape_with_scrapling("200003655", max_results=10)

    assert mock_sub.call_count == 3
    assert mock_sleep.call_count == 2
    assert products == []


@pytest.mark.asyncio
async def test_scrapling_retry_on_exception_attempts_again():
    """Exceção na 1ª tentativa → retry → JS data na 2ª → retorna produtos."""
    with patch("asyncio.sleep"):
        with patch(
            "subprocess.run",
            side_effect=[Exception("timeout"), _make_curl_result(_full_html())],
        ) as mock_sub:
            products = await _scrape_with_scrapling("200003655", max_results=10)

    assert mock_sub.call_count == 2
    assert len(products) == 1


@pytest.mark.asyncio
async def test_scrapling_all_exceptions_returns_empty():
    """3 exceções consecutivas → retorna []."""
    with patch("asyncio.sleep"):
        with patch("subprocess.run", side_effect=Exception("refused")) as mock_sub:
            products = await _scrape_with_scrapling("200003655", max_results=10)

    assert mock_sub.call_count == 3
    assert products == []
