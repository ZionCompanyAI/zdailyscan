# [TASK-061] fix(scraper): json.loads em extracted_content do crawl4ai

## Objetivo
`GET /scrapers/aliexpress` retorna HTTP 500 porque `result.extracted_content` é uma
string JSON, mas o código a atribui direto a `list[dict]`. Ao iterar, cada `item` é
um caractere → `AttributeError: str object has no attribute get`.

## Pacote / Módulo
`app/scrapers/aliexpress.py` → função `_scrape_with_crawl4ai()` — linha 44.

## Contratos (Referências Técnicas)

```python
# ANTES (linha 44) — BUG
raw: list[dict] = result.extracted_content or []

# DEPOIS — fix
import json
raw_content = result.extracted_content or "[]"
raw: list[dict] = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
```

## Detalhes de Implementação
- Apenas a linha 44 de `_scrape_with_crawl4ai` é afetada.
- `json` já está na stdlib — nenhuma dependência nova.
- Manter `try/except (ValueError, TypeError)` existente no loop — já cobre falhas de item individual.

## Tasks
- [x] Criar spec
- [x] RED: escrever teste que falha com string JSON como extracted_content
- [x] GREEN: aplicar json.loads fix
- [x] REFACTOR: limpar se necessário
- [x] Verify: suite completa verde
- [x] Archive

## Critérios de Verificação
- Teste novo `test_extracted_content_as_string` passa após fix
- `pytest tests/test_scraper.py tests/test_scraper_endpoint.py -x` verde
- `GET /scrapers/aliexpress` retorna 200 em produção
