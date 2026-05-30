# TASK-085 test: cobrir gaps que deixaram regressions #81/#82 passarem no CI

## Objetivo
Adicionar testes de regressão que documentem os invariantes quebrados pelas regressões #81 e #82, cobrindo 4 gaps de cobertura no CI.

## Pacote / Módulo
- `tests/test_scraper_regressions.py` — arquivo novo (canonical para regressões de scraper)
- `tests/test_scraper_endpoint.py` — adicionar teste de contagem real (Gap 4)

## Contratos (Referências Técnicas)

```python
# Gap 1 — default min_rating deve ser 0.0
sig = inspect.signature(get_hot_products)
assert sig.parameters["min_rating"].default == 0.0

# Gap 2 — SCRAPER_MODE=firecrawl chama firecrawl diretamente
mock_c4a.assert_not_called()
mock_fc.assert_called_once()

# Gap 3 — default min_rating inclui produtos com rating < 4.9
ratings = [p.rating for p in results]
assert any(r < 4.9 for r in ratings)

# Gap 4 — endpoint retorna count > 0
assert data["count"] > 0
```

## Tasks (checklist de execução)
- [x] Criar tests/test_scraper_regressions.py com Gap 1 + Gap 2 + Gap 3
- [x] Adicionar Gap 4 em tests/test_scraper_endpoint.py
- [x] Rodar pytest -x — todos devem passar
- [x] Rodar ruff check

## Critérios de Verificação
```bash
grep -q "default_min_rating" tests/test_scraper_regressions.py
grep -rq "assert_not_called" tests/
python3 -m pytest tests/ -x -q 2>&1 | tail -3
ruff check . --select I,E,F
```
