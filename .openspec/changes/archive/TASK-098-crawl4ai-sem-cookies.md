# [TASK-098] fix(scraper): crawl4ai chamado mesmo sem cookies

## Objetivo
O `get_hot_products()` no modo `crawl4ai` deve sempre tentar `_scrape_with_crawl4ai()` primeiro,
independente de `ALIEXPRESS_SESSION_COOKIES` estar definido ou não. O Firecrawl fica como fallback
apenas quando crawl4ai retorna lista vazia.

## Pacote / Módulo
`app/scrapers/aliexpress.py` → função `get_hot_products()`

## Contratos (Referências Técnicas)

```python
async def get_hot_products(
    category_id: str, min_rating: float = 0.0, max_results: int = 100
) -> list[AliProduct]:
    # MODO crawl4ai (default):
    # 1. Chamar _scrape_with_crawl4ai(category_id, max_results, session_cookies)
    #    session_cookies pode ser "" — crawl4ai funciona headless sem cookies
    # 2. Se retornar [] e firecrawl_url definida → fallback Firecrawl
    # 3. NÃO verificar session_cookies antes de chamar crawl4ai
```

## Detalhes de Implementação
- Remover o `if session_cookies:` que guarda crawl4ai
- Sempre chamar `_scrape_with_crawl4ai(category_id, max_results, session_cookies)` — o próprio
  `_scrape_with_crawl4ai` já lida com `session_cookies=""` (não injeta cookies)
- Manter lógica de fallback Firecrawl quando crawl4ai retorna []
- Atualizar `test_issue75_cookie_routing.py` — dois testes documentam o comportamento bugado

## Tasks
- [x] Criar tests/test_issue98_crawl4ai_no_cookies.py (RED)
- [x] Confirmar testes falham
- [x] Corrigir bug em app/scrapers/aliexpress.py (GREEN)
- [x] Atualizar test_issue75_cookie_routing.py (REFACTOR)
- [x] Rodar suite completa

## Critérios de Verificação
```bash
pytest tests/test_issue98_crawl4ai_no_cookies.py -v   # todos PASS
pytest tests/test_issue75_cookie_routing.py -v        # todos PASS (após update)
pytest tests/ -x                                       # suite completa PASS
```
