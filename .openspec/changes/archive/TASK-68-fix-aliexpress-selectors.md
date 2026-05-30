# [TASK-68] fix(scraper): CSS selectors AliExpress desatualizados

## Objetivo
Substituir seletores CSS gerados por bundler (com hashes instáveis) por seletores
baseados em atributos parciais de classe ou `data-*` attributes. Adicionar lógica
de fallback para Firecrawl quando `_scrape_with_crawl4ai` retorna lista vazia.

## Pacote / Módulo
`app/scrapers/aliexpress.py` — schema e função `get_hot_products()`

## Contratos

```python
# Schema extraído para constante de módulo
_PRODUCT_SCHEMA: dict  # acessível para testes sem importar crawl4ai

# Seletores não devem conter hashes webpack do padrão --[A-Za-z0-9]{6,}
# Usar [class*="base--name"] em vez de .base--name--HASH

# get_hot_products deve chamar firecrawl quando crawl4ai retorna lista vazia
async def get_hot_products(
    category_id: str, min_rating: float = 4.9, max_results: int = 100
) -> list[AliProduct]: ...
```

## Detalhes de Implementação
- Extrair schema para `_PRODUCT_SCHEMA` (nível de módulo, lazy-import de crawl4ai continua)
- Usar `[class*="list--item--"]` como baseSelector em vez de `.list--item--HASH`
- Usar `[class*="multi--titleText"]`, `[class*="multi--price-sale"]`, etc. para fields
- Em `get_hot_products`: se `products == []` e `firecrawl_url`, chamar fallback (não apenas em Exception)

## Tasks
- [x] Escrever testes RED que falham
- [x] Implementar GREEN (schema estável + fallback-on-empty)
- [x] REFACTOR + lint
- [x] Suite completa verde

## Critérios de Verificação
1. `test_product_schema_no_dynamic_hashes` passa (schema sem `--[A-Za-z0-9]{6,}`)
2. `test_empty_crawl4ai_triggers_firecrawl` passa (fallback chamado quando lista vazia)
3. `ruff check app/scrapers/aliexpress.py --select I,E,F` sem erros
4. Suite completa `pytest tests/test_scraper.py tests/test_issue68_selectors.py` verde
