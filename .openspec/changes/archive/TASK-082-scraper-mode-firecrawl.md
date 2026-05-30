# [TASK-082] fix(scraper): SCRAPER_MODE=firecrawl ignorado

## Objetivo
`get_hot_products` deve respeitar `SCRAPER_MODE=firecrawl`: se o mode for `firecrawl` e
`FIRECRAWL_URL` estiver setado, usar Firecrawl diretamente sem tentar crawl4ai.
Atualmente o código ignora esse mode e sempre tenta crawl4ai primeiro (bot detection latency).

## Pacote / Módulo
`app/scrapers/aliexpress.py` → função `get_hot_products()`

## Contratos

```python
async def get_hot_products(
    category_id: str, min_rating: float = 0.0, max_results: int = 100
) -> list[AliProduct]:
    mode = os.environ.get("SCRAPER_MODE", "crawl4ai")

    if mode == "firecrawl":
        if firecrawl_url:
            return filtered_firecrawl_results  # sem crawl4ai
        # fallthrough para default se não há FIRECRAWL_URL
    elif mode == "mock":
        return get_mock_products(...)

    # Default: crawl4ai (com cookies se setado), fallback firecrawl
```

## Detalhes de Implementação
- Adicionar branch `if mode == "firecrawl":` antes do `if mode == "mock":`
- Quando `mode == "firecrawl"` e `firecrawl_url` definida: chamar `get_products_via_firecrawl`, aplicar filtro `min_rating`, retornar
- Quando `mode == "firecrawl"` e sem URL: fallthrough para o bloco default (crawl4ai)
- `mock` vira `elif mode == "mock":`
- Default permanece igual (crawl4ai com cookies → fallback firecrawl)

## Tasks
- [x] Escrever testes RED cobrindo: firecrawl mode usa firecrawl, firecrawl mode sem URL usa crawl4ai default, mock não chama crawl4ai/firecrawl
- [x] Implementar branch firecrawl no get_hot_products (GREEN)
- [x] Refactor: limpar código, garantir testes verdes

## Critérios de Verificação
- `grep -q 'mode == .firecrawl.' app/scrapers/aliexpress.py`
- `python3 -m pytest tests/ -x -q` — todos passam
- `ruff check . --select I,E,F` — zero erros
