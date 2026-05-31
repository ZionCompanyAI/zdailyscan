"""Tests for issue #91 — Firecrawl httpx timeout and %r logger fix."""
import logging
from unittest.mock import AsyncMock, patch

import pytest


# ── Acceptance criteria from spec ─────────────────────────────────────────────

def test_firecrawl_uses_180s_httpx_timeout():
    """httpx client.post must use timeout=180.0, not 60.0."""
    import ast
    import pathlib

    source = pathlib.Path("app/scrapers/fallback_firecrawl.py").read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "timeout":
                    val = kw.value
                    if isinstance(val, ast.Constant):
                        assert val.value == 180.0, (
                            f"Expected timeout=180.0, got timeout={val.value}"
                        )
                    return
    pytest.fail("No keyword argument 'timeout' found in fallback_firecrawl.py")


def test_firecrawl_body_contains_150000ms_timeout():
    """Firecrawl JSON body must include 'timeout': 150000."""
    import pathlib

    source = pathlib.Path("app/scrapers/fallback_firecrawl.py").read_text()
    assert "150000" in source, (
        "Expected Firecrawl body to contain timeout 150000ms"
    )


def test_pipeline_logger_uses_repr_for_exception():
    """`pipeline.py` scraper warning must use %r to show blank exceptions."""
    import pathlib

    source = pathlib.Path("app/pipeline.py").read_text()
    assert "scraper failed for category %s: %r" in source, (
        "Expected pipeline.py scraper warning to use %r (not %s)"
    )


# ── Behavioural: blank TimeoutException is now visible in logs ─────────────────

@pytest.mark.asyncio
async def test_timeout_exception_repr_visible_in_logs(caplog):
    """TimeoutException with blank str() shows as repr in pipeline warning log."""
    import httpx

    # TimeoutException has an empty str()
    blank_exc = httpx.TimeoutException("")
    assert str(blank_exc) == ""

    with patch("app.pipeline.get_hot_products", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.side_effect = blank_exc

        from app import pipeline

        with caplog.at_level(logging.WARNING, logger="app.pipeline"):
            await pipeline.run_daily_scan(
                scan_id="test-91",
                categories=["200003655"],
            )

    # The repr of a blank TimeoutException should appear in the log
    assert any(
        "TimeoutException" in r.message for r in caplog.records
    ), f"Expected 'TimeoutException' in logs, got: {[r.message for r in caplog.records]}"
