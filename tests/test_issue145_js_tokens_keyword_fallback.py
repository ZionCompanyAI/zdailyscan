"""Issue #145 — JS undefined/NaN sanitization + keyword multi-pattern fallback."""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.scrapers.aliexpress import _scrape_with_scrapling

_PRODUCT_ITEM = {
    "productId": "99901",
    "title": {"displayTitle": "USB-C Hub"},
    "prices": {"salePrice": {"minPrice": 9.99}},
    "star_rating": "4.7",
    "real_trade_count": "500",
    "image": {"imgUrl": "//ae01.alicdn.com/kf/hub.jpg"},
}


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


def _html_with_init_data(payload_str: str) -> str:
    return (
        f"<html><script>window._dida_config_._init_data_ = {payload_str};"
        "</script></html>"
    )


def _html_with_run_params(payload_str: str) -> str:
    return (
        f"<html><script>window.runParams = {payload_str};"
        "</script></html>"
    )


# --- Fix 1: JS token sanitization ---

@pytest.mark.asyncio
async def test_scrapling_undefined_in_json_does_not_crash():
    """undefined em _init_data_ é substituído por null antes do parse."""
    payload = json.dumps({"data": {"resultList": [_PRODUCT_ITEM]}})
    # Inject JS undefined into a field value
    payload_with_undefined = payload.replace('"4.7"', "undefined")
    html = _html_with_init_data(payload_with_undefined)

    with patch("subprocess.run", return_value=_make_curl_result(html)):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    # Should not raise, should return product (with rating 0 or 4.7 depending on parse)
    assert len(products) == 1
    assert products[0].product_id == "99901"


@pytest.mark.asyncio
async def test_scrapling_nan_in_json_does_not_crash():
    """NaN em _init_data_ é substituído por null antes do parse."""
    payload = json.dumps({"data": {"resultList": [_PRODUCT_ITEM]}})
    payload_with_nan = payload.replace('"4.7"', "NaN")
    html = _html_with_init_data(payload_with_nan)

    with patch("subprocess.run", return_value=_make_curl_result(html)):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    assert products[0].product_id == "99901"


@pytest.mark.asyncio
async def test_scrapling_infinity_in_json_does_not_crash():
    """Infinity em _init_data_ é substituído por null antes do parse."""
    payload = json.dumps({"data": {"resultList": [_PRODUCT_ITEM]}})
    payload_with_inf = payload.replace('"4.7"', "Infinity")
    html = _html_with_init_data(payload_with_inf)

    with patch("subprocess.run", return_value=_make_curl_result(html)):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    assert products[0].product_id == "99901"


@pytest.mark.asyncio
async def test_scrapling_multiple_js_tokens_in_json():
    """Múltiplos tokens JS (undefined, NaN, Infinity) são todos substituídos."""
    raw_json = (
        '{"data": {"resultList": [{"productId": "777", '
        '"title": {"displayTitle": undefined}, '
        '"prices": {"salePrice": {"minPrice": NaN}}, '
        '"star_rating": Infinity, '
        '"real_trade_count": "100", '
        '"image": {"imgUrl": "//ae01.alicdn.com/kf/img.jpg"}}]}}'
    )
    html = _html_with_init_data(raw_json)

    with patch("subprocess.run", return_value=_make_curl_result(html)):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    assert products[0].product_id == "777"


# --- Fix 2: multi-pattern keyword fallback ---

@pytest.mark.asyncio
async def test_scrapling_keyword_falls_back_to_run_params():
    """Com keyword, se _init_data_ ausente, tenta window.runParams."""
    payload = json.dumps({"data": {"resultList": [_PRODUCT_ITEM]}})
    html = _html_with_run_params(payload)

    with patch("subprocess.run", return_value=_make_curl_result(html)):
        products = await _scrape_with_scrapling("", max_results=10, keyword="USB-C adapter")

    assert len(products) == 1
    assert products[0].product_id == "99901"


@pytest.mark.asyncio
async def test_scrapling_init_data_takes_priority_over_run_params():
    """_init_data_ tem prioridade sobre window.runParams quando ambos presentes."""
    item_init = {**_PRODUCT_ITEM, "productId": "INIT"}
    item_run = {**_PRODUCT_ITEM, "productId": "RUN"}
    payload_init = json.dumps({"data": {"resultList": [item_init]}})
    payload_run = json.dumps({"data": {"resultList": [item_run]}})
    html = (
        f"<html><script>"
        f"window._dida_config_._init_data_ = {payload_init};"
        f"window.runParams = {payload_run};"
        f"</script></html>"
    )

    with patch("subprocess.run", return_value=_make_curl_result(html)):
        products = await _scrape_with_scrapling("", max_results=10, keyword="test")

    assert len(products) == 1
    assert products[0].product_id == "INIT"


@pytest.mark.asyncio
async def test_scrapling_no_pattern_found_returns_empty():
    """Se nenhum padrão JS é encontrado, retorna [] sem crash."""
    html = "<html><script>window.foo = 1;</script></html>"

    with patch("subprocess.run", return_value=_make_curl_result(html)):
        products = await _scrape_with_scrapling("", max_results=10, keyword="test")

    assert products == []
