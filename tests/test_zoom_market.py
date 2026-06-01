import asyncio
import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.analyzers.mercado_livre import search_br_market_via_zoom

NEXT_DATA = json.dumps({
    "props": {"initialReduxState": {"hits": {"hits": [
        {"price": 1000, "name": "A", "url": "/a"},
        {"price": 2000, "name": "B", "url": "/b"},
        {"price": 1500, "name": "C", "url": "/c"},
    ]}}},
    "page": "/search",
    "query": {},
})
MOCK_HTML = f'"__NEXT_DATA__" type="application/json">{NEXT_DATA}</script><p>3 resultados</p>'


def _mk_client(html):
    resp = MagicMock()
    resp.text = html
    resp.raise_for_status = MagicMock()
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.get = AsyncMock(return_value=resp)
    return client


def test_zoom_parses_prices():
    with patch("httpx.AsyncClient", return_value=_mk_client(MOCK_HTML)):
        r = asyncio.run(search_br_market_via_zoom("smartphone"))
    assert r.found is True
    assert r.avg_price_brl == pytest.approx(1500.0)
    assert r.min_price_brl == 1000.0
    assert r.max_price_brl == 2000.0
    assert r.result_count == 3


def test_zoom_not_found_on_empty():
    with patch("httpx.AsyncClient", return_value=_mk_client("<html></html>")):
        r = asyncio.run(search_br_market_via_zoom("xyz"))
    assert r.found is False


def test_zoom_truncates_long_title_to_5_words():
    """Long AliExpress titles must be truncated to 5 words before querying Zoom."""
    long_title = (
        "Summer Women Thin Sunscreen Cardigan Lace-up Knitwear Tops Female Korean "
        "Style Lantern Sleeve Short Coat Casual Sun Protected"
    )
    client = _mk_client(MOCK_HTML)
    with patch("httpx.AsyncClient", return_value=client):
        asyncio.run(search_br_market_via_zoom(long_title))

    sent_q = client.get.call_args.kwargs["params"]["q"]
    assert sent_q == "Summer Women Thin Sunscreen Cardigan"
    assert len(sent_q.split()) == 5
