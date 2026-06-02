# [TASK-150] fix(scraper) — Accept-Encoding + retry 3x em _scrape_with_scrapling

## Objetivo
httpx não envia Accept-Encoding por padrão, fazendo AliExpress servir thin pages sem dados JS.
Adicionar headers browser-completos e retry de 3 tentativas com 4s de sleep entre elas.

## Pacote / Módulo
`app/scrapers/aliexpress.py` — duas mudanças:
1. `_SCRAPLING_HEADERS` dict (linhas ~235-243)
2. Bloco de request em `_scrape_with_scrapling` → loop de 3 tentativas

## Contratos

```python
_SCRAPLING_HEADERS: dict[str, str]  # deve conter Accept-Encoding, Connection, Sec-Fetch-Dest

async def _scrape_with_scrapling(category_id: str, max_results: int, keyword: str = "") -> list[AliProduct]:
    # retry: até 3 tentativas; asyncio.sleep(4) entre elas; retorna [] se todas falharem
```

## Tasks
- [x] Atualizar `_SCRAPLING_HEADERS` com os 10 headers listados na issue
- [x] Refatorar bloco de request em `_scrape_with_scrapling` para loop de 3 tentativas com `asyncio.sleep(4)`
- [x] `pytest tests/ -x -q` verde

## Critérios de Verificação
- `_SCRAPLING_HEADERS` contém `Accept-Encoding`, `Sec-Fetch-Dest`, `Connection`
- Lógica de retry (loop de 3 tentativas) presente em `_scrape_with_scrapling`
- `pytest tests/ -x -q` passa sem regressões
