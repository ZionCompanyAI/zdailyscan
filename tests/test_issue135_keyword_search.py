import os
import importlib
import inspect
import pytest


def test_get_active_keywords_default():
    import app.pipeline as mod
    importlib.reload(mod)
    keywords = mod.get_active_keywords()
    assert len(keywords) >= 5
    assert any("USB" in k for k in keywords)


def test_get_active_keywords_from_env(monkeypatch):
    monkeypatch.setenv("SCAN_KEYWORDS", "USB-C,HDMI adapter")
    import app.pipeline as mod
    importlib.reload(mod)
    assert mod.get_active_keywords() == ["USB-C", "HDMI adapter"]


def test_firecrawl_url_uses_wholesale_when_keyword():
    import app.scrapers.aliexpress as mod
    src = inspect.getsource(mod._scrape_with_firecrawl)
    assert "wholesale" in src
    assert "SearchText" in src
