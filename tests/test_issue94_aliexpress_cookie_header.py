"""Tests for issue #94 — ALIEXPRESS_SESSION_COOKIES Cookie header + aliexpress.us URL."""
import json
import pathlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


SOURCE = pathlib.Path("app/scrapers/fallback_firecrawl.py")


# ── Static acceptance criteria ─────────────────────────────────────────────────

def test_url_uses_aliexpress_us():
    """URL target must use aliexpress.us, not aliexpress.com."""
    source = SOURCE.read_text()
    assert "aliexpress.us" in source, "Expected aliexpress.us in fallback_firecrawl.py"
    assert "aliexpress.com" not in source, "aliexpress.com must be removed from fallback_firecrawl.py"


def test_env_var_name_present():
    """ALIEXPRESS_SESSION_COOKIES env var must be referenced in the scraper."""
    source = SOURCE.read_text()
    assert "ALIEXPRESS_SESSION_COOKIES" in source, (
        "Expected ALIEXPRESS_SESSION_COOKIES to be read in fallback_firecrawl.py"
    )


# ── Behavioural: Cookie header injection ───────────────────────────────────────

@pytest.mark.asyncio
async def test_cookie_header_injected_from_env():
    """When ALIEXPRESS_SESSION_COOKIES is set, Cookie header must be sent."""
    cookies = [
        {"name": "xman_us_f", "value": "abc123"},
        {"name": "_tbtoken", "value": "xyz"},
    ]
    env = {
        "FIRECRAWL_API_KEY": "",
        "ALIEXPRESS_SESSION_COOKIES": json.dumps(cookies),
    }

    captured_headers = {}

    async def fake_post(url, *, headers, json, timeout):
        captured_headers.update(headers)
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"data": {"extract": []}}
        return mock_resp

    with patch.dict("os.environ", env, clear=False):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=fake_post)
            mock_client_cls.return_value = mock_client

            import importlib
            import app.scrapers.fallback_firecrawl as mod
            importlib.reload(mod)

            await mod.get_products_via_firecrawl("200003655", "http://fake-firecrawl")

    assert "Cookie" in captured_headers, "Cookie header was not set"
    assert "xman_us_f=abc123" in captured_headers["Cookie"]
    assert "_tbtoken=xyz" in captured_headers["Cookie"]


@pytest.mark.asyncio
async def test_cookie_header_absent_when_env_not_set():
    """When ALIEXPRESS_SESSION_COOKIES is not set, Cookie header must not be sent."""
    captured_headers = {}

    async def fake_post(url, *, headers, json, timeout):
        captured_headers.update(headers)
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"data": {"extract": []}}
        return mock_resp

    env_patch = {"FIRECRAWL_API_KEY": ""}

    with patch.dict("os.environ", env_patch, clear=False):
        # Ensure the var is absent
        import os
        os.environ.pop("ALIEXPRESS_SESSION_COOKIES", None)

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=fake_post)
            mock_client_cls.return_value = mock_client

            import importlib
            import app.scrapers.fallback_firecrawl as mod
            importlib.reload(mod)

            await mod.get_products_via_firecrawl("200003655", "http://fake-firecrawl")

    assert "Cookie" not in captured_headers, "Cookie header should not be set when env var is missing"


@pytest.mark.asyncio
async def test_malformed_cookies_env_does_not_raise():
    """Malformed ALIEXPRESS_SESSION_COOKIES must be silently ignored (no exception)."""
    env = {
        "FIRECRAWL_API_KEY": "",
        "ALIEXPRESS_SESSION_COOKIES": "not-valid-json!!!",
    }

    async def fake_post(url, *, headers, json, timeout):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"data": {"extract": []}}
        return mock_resp

    with patch.dict("os.environ", env, clear=False):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=fake_post)
            mock_client_cls.return_value = mock_client

            import importlib
            import app.scrapers.fallback_firecrawl as mod
            importlib.reload(mod)

            # Must not raise
            result = await mod.get_products_via_firecrawl("200003655", "http://fake-firecrawl")
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_cookies_without_value_are_filtered():
    """Cookies with empty/missing value must be excluded from the Cookie header."""
    cookies = [
        {"name": "valid_cookie", "value": "goodval"},
        {"name": "empty_cookie", "value": ""},
        {"name": "no_value_cookie"},
    ]
    env = {
        "FIRECRAWL_API_KEY": "",
        "ALIEXPRESS_SESSION_COOKIES": json.dumps(cookies),
    }

    captured_headers = {}

    async def fake_post(url, *, headers, json, timeout):
        captured_headers.update(headers)
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"data": {"extract": []}}
        return mock_resp

    with patch.dict("os.environ", env, clear=False):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=fake_post)
            mock_client_cls.return_value = mock_client

            import importlib
            import app.scrapers.fallback_firecrawl as mod
            importlib.reload(mod)

            await mod.get_products_via_firecrawl("200003655", "http://fake-firecrawl")

    assert "Cookie" in captured_headers
    assert "valid_cookie=goodval" in captured_headers["Cookie"]
    assert "empty_cookie" not in captured_headers["Cookie"]
    assert "no_value_cookie" not in captured_headers["Cookie"]
