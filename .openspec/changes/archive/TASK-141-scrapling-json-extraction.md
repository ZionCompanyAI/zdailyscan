# [TASK-141] fix(scrapling): extrair produtos de window._dida_config_._init_data_

## Objetivo
Substituir CSS selectors DOM no `_scrape_with_scrapling()` por extração de JSON embutido no HTML inicial (`window._dida_config_._init_data_`), que contém 60+ produtos sem necessidade de JS rendering.

## Pacote / Módulo
`app/scrapers/aliexpress.py` — funções `_scrape_with_scrapling()` e nova `_find_product_list()`

## Contratos

```python
def _find_product_list(data: dict | list) -> list:
    """Busca recursivamente a lista que contém productId nos dicts."""
    ...

async def _scrape_with_scrapling(
    category_id: str, max_results: int, keyword: str = ""
) -> list[AliProduct]:
    """
    Usa Fetcher.get() + regex para extrair _init_data_ do HTML inicial.
    Não usa CSS selectors. Não usa StealthyFetcher.
    """
    ...
```

## Detalhes de Implementação
- Usar `scrapling.Fetcher.get()` (síncrono, HTTP simples com headers)
- Regex: `window\._dida_config_\._init_data_\s*=\s*(\{.+?\});` com `re.DOTALL`
- Campos: productId, title.displayTitle, prices.salePrice.minPrice, star_rating, real_trade_count, image.imgUrl
- `_find_product_list()` busca recursivamente — path exato pode variar no JSON real

## Tasks
- [x] Escrever testes RED (test_issue141_scrapling_json.py)
- [x] Executar testes — FALHAM (RED confirmado)
- [x] Implementar `_find_product_list()` e nova `_scrape_with_scrapling()`
- [x] Executar testes — PASSAM (GREEN confirmado)
- [x] Atualizar testes CSS legados em test_issue139_scrapling.py
- [x] REFACTOR + suite completa verde

## Critérios de Verificação
- `_find_product_list()` encontra lista com productId em qualquer profundidade
- `_scrape_with_scrapling()` extrai produtos do JSON `_init_data_`
- Retorna [] quando `_init_data_` ausente no HTML
- Retorna [] em exceção
- Skipa itens sem productId ou title
- Não usa CSS selectors
