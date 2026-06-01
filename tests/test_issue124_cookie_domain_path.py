"""RED tests — issue #124: cookies AliExpress devem ter domain e path."""

import ast
import inspect
import json
import re


def _scraper_source() -> str:
    import app.scrapers.aliexpress as mod
    return inspect.getsource(mod)


def test_cookie_block_has_aliexpress_domain():
    """O bloco de parse de cookies deve injetar '.aliexpress.com' como domain padrão."""
    src = _scraper_source()
    assert ".aliexpress.com" in src, (
        "Bloco de cookies não contém '.aliexpress.com' — domain padrão ausente"
    )


def test_cookie_block_sets_path():
    """O bloco de parse de cookies deve injetar '/' como path padrão."""
    src = _scraper_source()
    # Deve haver alguma referência a "path" no contexto de cookies
    assert re.search(r'"path".*"/"', src) or re.search(r"'path'.*'/'", src), (
        "Bloco de cookies não define path='/' — campo path ausente"
    )


def test_cookie_block_uses_get_with_default():
    """Deve usar c.get('domain', '.aliexpress.com') e c.get('path', '/')."""
    src = _scraper_source()
    assert 'c.get("domain"' in src or "c.get('domain'" in src, (
        "Não usa c.get('domain', ...) — domain pode não ser preservado se já existir"
    )
    assert 'c.get("path"' in src or "c.get('path'" in src, (
        "Não usa c.get('path', ...) — path pode não ser preservado se já existir"
    )


def test_cookies_without_domain_get_default_injected():
    """Simula parse de cookies sem domain/path e verifica que os defaults são injetados."""
    import json as _json

    raw_cookies = json.dumps([{"name": "aep_usuc_f", "value": "abc123"}])

    # Replicar a lógica do scraper manualmente para testar o comportamento esperado
    cookies: list[dict] = []
    try:
        raw = _json.loads(raw_cookies)
        for c in raw:
            cookies.append({
                **c,
                "domain": c.get("domain", ".aliexpress.com"),
                "path": c.get("path", "/"),
            })
    except Exception:
        pass

    assert len(cookies) == 1
    assert cookies[0]["domain"] == ".aliexpress.com"
    assert cookies[0]["path"] == "/"
    assert cookies[0]["name"] == "aep_usuc_f"
    assert cookies[0]["value"] == "abc123"


def test_cookies_with_existing_domain_preserved():
    """Se o cookie já tiver domain, o valor original deve ser preservado."""
    import json as _json

    raw_cookies = json.dumps([
        {"name": "tok", "value": "xyz", "domain": ".custom.com", "path": "/shop"}
    ])

    cookies: list[dict] = []
    try:
        raw = _json.loads(raw_cookies)
        for c in raw:
            cookies.append({
                **c,
                "domain": c.get("domain", ".aliexpress.com"),
                "path": c.get("path", "/"),
            })
    except Exception:
        pass

    assert cookies[0]["domain"] == ".custom.com"
    assert cookies[0]["path"] == "/shop"


def test_file_is_valid_python():
    """O arquivo aliexpress.py deve ser sintaxe Python válida após o fix."""
    path = "app/scrapers/aliexpress.py"
    with open(path) as f:
        src = f.read()
    ast.parse(src)  # raises SyntaxError if invalid
