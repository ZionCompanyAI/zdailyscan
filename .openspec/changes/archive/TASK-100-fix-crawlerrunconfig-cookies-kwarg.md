# [TASK-100] fix: CrawlerRunConfig no longer accepts cookies kwarg

## Objetivo
`_scrape_with_crawl4ai()` falha com `TypeError: CrawlerRunConfig.__init__() got an unexpected keyword argument 'cookies'` porque o parâmetro foi removido da API do crawl4ai >= 0.4.0. Qualquer chamada com `SCRAPER_MODE=crawl4ai` retorna `total_scanned=0`.

## Pacote / Módulo
`app/scrapers/aliexpress.py` → função `_scrape_with_crawl4ai()`

## Contratos (Referências Técnicas)

```python
# ANTES (linha 58) — quebrado
run_config = CrawlerRunConfig(extraction_strategy=strategy, cookies=cookies)

# DEPOIS — correto
run_config = CrawlerRunConfig(extraction_strategy=strategy)
# cookies= removido; BrowserConfig(headless=True) inalterado
```

A lógica de parse de cookies (linhas 51–56) torna-se dead code e deve ser removida.

## Detalhes de Implementação
- Remover `cookies=cookies` do `CrawlerRunConfig(...)`.
- Remover o bloco de parse de cookies (variável `cookies: list[dict] | None = None` + bloco `if session_cookies`).
- `session_cookies` continua como parâmetro de `_scrape_with_crawl4ai()` (assinatura pública preservada — callers externos podem depender dela).
- Sem tentativa de passar cookies via `BrowserConfig` (a necessidade foi descartada — AliExpress público não exige cookies autenticados para scraping headless).

## Tasks (checklist de execução)
- [x] RED: escrever teste que confirma TypeError quando `cookies=` é passado para `CrawlerRunConfig` stub
- [x] GREEN: remover `cookies=cookies` de `CrawlerRunConfig(...)` e o bloco de parse morto
- [x] REFACTOR: garantir que nenhum dead code sobrou; rodar suite completa

## Critérios de Verificação
- `_scrape_with_crawl4ai()` executa sem TypeError mesmo com `session_cookies` non-empty
- Retorna `list[AliProduct]` (pode ser vazia — não exceção)
- `pytest tests/` verde (todos os testes existentes passam)
- Novo teste `test_crawl4ai_no_cookies_kwarg_in_run_config` RED → GREEN durante o ciclo
