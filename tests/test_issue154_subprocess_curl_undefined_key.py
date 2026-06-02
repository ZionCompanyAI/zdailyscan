"""Issue #154 — subprocess curl + corrigir undefined-como-chave JSON em _scrape_with_scrapling."""
import json
import re
from unittest.mock import MagicMock, patch

import pytest

from app.scrapers.aliexpress import _scrape_with_scrapling

_PRODUCT_ITEM = {
    "productId": "99001",
    "title": {"displayTitle": "Curl Widget"},
    "prices": {"salePrice": {"minPrice": 12.5}},
    "star_rating": "4.7",
    "real_trade_count": "500",
    "image": {"imgUrl": "//ae01.alicdn.com/kf/curl.jpg"},
}

_INIT_DATA = {"data": {"resultList": [_PRODUCT_ITEM]}}


def _full_html(data: dict | None = None) -> str:
    if data is None:
        data = _INIT_DATA
    return (
        f"<html><script>window._dida_config_._init_data_ = {json.dumps(data)};"
        "</script></html>"
    )


def _thin_html() -> str:
    return "<html><body>Loading...</body></html>"


def _make_curl_result(html: str, returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = html.encode("utf-8")
    return result


# ---------------------------------------------------------------------------
# subprocess.run is used (not httpx.get)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrapling_uses_subprocess_not_httpx():
    """_scrape_with_scrapling deve chamar subprocess.run, não httpx.get."""
    curl_result = _make_curl_result(_full_html())

    with patch("subprocess.run", return_value=curl_result) as mock_sub:
        with patch("httpx.get") as mock_httpx:
            products = await _scrape_with_scrapling("200003655", max_results=10)

    mock_sub.assert_called()
    mock_httpx.assert_not_called()
    assert len(products) == 1


@pytest.mark.asyncio
async def test_scrapling_curl_command_includes_compressed():
    """O comando curl deve incluir --compressed."""
    curl_result = _make_curl_result(_full_html())

    with patch("subprocess.run", return_value=curl_result) as mock_sub:
        await _scrape_with_scrapling("200003655", max_results=10)

    cmd = mock_sub.call_args[0][0]
    assert "--compressed" in cmd
    assert "curl" in cmd[0]


@pytest.mark.asyncio
async def test_scrapling_curl_command_includes_max_time():
    """O comando curl deve incluir --max-time."""
    curl_result = _make_curl_result(_full_html())

    with patch("subprocess.run", return_value=curl_result) as mock_sub:
        await _scrape_with_scrapling("200003655", max_results=10)

    cmd = mock_sub.call_args[0][0]
    assert "--max-time" in cmd


# ---------------------------------------------------------------------------
# curl returncode != 0 → html vazio → retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrapling_curl_nonzero_returncode_retries():
    """returncode != 0 → html vazio → retry → sucesso na 2ª tentativa."""
    fail_result = _make_curl_result("", returncode=1)
    ok_result = _make_curl_result(_full_html())

    with patch("asyncio.sleep"):
        with patch("subprocess.run", side_effect=[fail_result, ok_result]) as mock_sub:
            products = await _scrape_with_scrapling("200003655", max_results=10)

    assert mock_sub.call_count == 2
    assert len(products) == 1


@pytest.mark.asyncio
async def test_scrapling_curl_exception_retries():
    """Exceção no subprocess.run → retry → sucesso na 2ª tentativa."""
    ok_result = _make_curl_result(_full_html())

    with patch("asyncio.sleep"):
        with patch("subprocess.run", side_effect=[Exception("curl not found"), ok_result]) as mock_sub:
            products = await _scrape_with_scrapling("200003655", max_results=10)

    assert mock_sub.call_count == 2
    assert len(products) == 1


@pytest.mark.asyncio
async def test_scrapling_all_curl_failures_returns_empty():
    """3 falhas curl consecutivas → retorna []."""
    fail_result = _make_curl_result("", returncode=1)

    with patch("asyncio.sleep"):
        with patch("subprocess.run", return_value=fail_result) as mock_sub:
            products = await _scrape_with_scrapling("200003655", max_results=10)

    assert mock_sub.call_count == 3
    assert products == []


# ---------------------------------------------------------------------------
# undefined-como-chave fix
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrapling_undefined_as_key_parsed_correctly():
    """JSON com undefined como chave deve ser parseado sem erro."""
    html_with_undefined_key = (
        "<html><script>window._dida_config_._init_data_ = "
        '{ undefined: {"productId": "77777", "title": {"displayTitle": "Key Test"},'
        ' "prices": {"salePrice": {"minPrice": 5.0}}, "star_rating": "4.0",'
        ' "real_trade_count": "100", "image": {"imgUrl": "//img.jpg"}} }; </script></html>'
    )
    curl_result = _make_curl_result(html_with_undefined_key)

    with patch("subprocess.run", return_value=curl_result):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    # Should not raise JSONDecodeError — may return 0 products (key is not productId)
    # but must not crash
    assert isinstance(products, list)


@pytest.mark.asyncio
async def test_scrapling_undefined_as_value_becomes_null():
    """JSON com undefined como VALOR → null → não causa JSONDecodeError."""
    html_with_undefined_value = (
        "<html><script>window._dida_config_._init_data_ = "
        '{"data": {"resultList": [{"productId": "88888", "title": {"displayTitle": "Val Test"},'
        ' "prices": {"salePrice": {"minPrice": undefined}},'
        ' "star_rating": undefined, "real_trade_count": "200",'
        ' "image": {"imgUrl": "//img.jpg"}}]}}; </script></html>'
    )
    curl_result = _make_curl_result(html_with_undefined_value)

    with patch("subprocess.run", return_value=curl_result):
        products = await _scrape_with_scrapling("200003655", max_results=10)

    # Must not raise — JSON with undefined values is parseable after regex fix
    assert isinstance(products, list)


# ---------------------------------------------------------------------------
# nixpacks.toml
# ---------------------------------------------------------------------------


def test_nixpacks_toml_exists_with_curl():
    """nixpacks.toml deve existir na raiz do projeto com nixPkgs = ['curl']."""
    import pathlib

    nixpacks = pathlib.Path(__file__).parent.parent / "nixpacks.toml"
    assert nixpacks.exists(), "nixpacks.toml não encontrado na raiz do projeto"
    content = nixpacks.read_text()
    assert "curl" in content


# ---------------------------------------------------------------------------
# Regex unit tests (não precisam de async)
# ---------------------------------------------------------------------------


def test_regex_undefined_key_converted_to_string():
    """re.sub step 1: undefined como chave → '_undefined_' (string JSON válida)."""
    raw = '{ undefined: {"val": 1} }'
    step1 = re.sub(r'([{,\[]\s*)undefined(\s*:)', r'\1"_undefined_"\2', raw)
    assert '"_undefined_"' in step1
    assert "null:" not in step1
    parsed = json.loads(step1)
    assert "_undefined_" in parsed


def test_regex_undefined_value_converted_to_null():
    """re.sub step 2: undefined como valor → null."""
    raw = '{"a": undefined, "b": 1}'
    step1 = re.sub(r'([{,\[]\s*)undefined(\s*:)', r'\1"_undefined_"\2', raw)
    step2 = re.sub(r'\bundefined\b', 'null', step1)
    parsed = json.loads(step2)
    assert parsed["a"] is None
    assert parsed["b"] == 1


def test_regex_two_step_combined():
    """Regex em 2 passos: undefined como chave E como valor no mesmo JSON."""
    raw = '{ undefined: undefined }'
    step1 = re.sub(r'([{,\[]\s*)undefined(\s*:)', r'\1"_undefined_"\2', raw)
    step2 = re.sub(r'\bundefined\b', 'null', step1)
    parsed = json.loads(step2)
    assert parsed["_undefined_"] is None
