"""Issue #147 — undefined as JSON key must be quoted, not replaced with bare null."""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.scrapers.aliexpress import _scrape_with_scrapling

_PRODUCT_ITEM = {
    "productId": "99902",
    "title": {"displayTitle": "Wireless Charger"},
    "prices": {"salePrice": {"minPrice": 12.50}},
    "star_rating": "4.5",
    "real_trade_count": "800",
    "image": {"imgUrl": "//ae01.alicdn.com/kf/charger.jpg"},
}


def _make_resp(html: str, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.status_code = status_code
    resp.raise_for_status.return_value = None
    return resp


@pytest.mark.asyncio
async def test_scrapling_undefined_as_key_does_not_crash():
    """undefined como CHAVE: { undefined: {...} } → {"undefined": {...}} — JSON válido."""
    inner = json.dumps({"data": {"resultList": [_PRODUCT_ITEM]}})
    # _init_data_ starts with `{ undefined: <inner> }` — undefined is the key
    raw_js = "{ undefined: " + inner + " }"
    html = f"<html><script>window._dida_config_._init_data_ = {raw_js};</script></html>"

    with patch("httpx.get", return_value=_make_resp(html)):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    assert products[0].product_id == "99902"


@pytest.mark.asyncio
async def test_scrapling_undefined_as_key_and_value_simultaneously():
    """undefined como CHAVE e como VALOR num mesmo documento."""
    # { undefined: {"productId": "99903", "star_rating": undefined, ...} }
    raw_js = (
        '{ undefined: {"data": {"resultList": [{'
        '"productId": "99903", '
        '"title": {"displayTitle": "Bluetooth Speaker"}, '
        '"prices": {"salePrice": {"minPrice": 8.99}}, '
        '"star_rating": undefined, '
        '"real_trade_count": "300", '
        '"image": {"imgUrl": "//ae01.alicdn.com/kf/spk.jpg"}'
        "}]}} }"
    )
    html = f"<html><script>window._dida_config_._init_data_ = {raw_js};</script></html>"

    with patch("httpx.get", return_value=_make_resp(html)):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    assert len(products) == 1
    assert products[0].product_id == "99903"


