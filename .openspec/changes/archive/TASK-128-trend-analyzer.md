# [TASK-128] feat: trend_analyzer — 1688.com + Google Trends BR para score_tendencia real

## Objetivo
Substituir `score_tendencia=0.5` hardcoded por score dinâmico calculado via scraping 1688.com (Firecrawl) e validação Google Trends BR (pytrends). Cache de 24h por keyword. Fallback para 0.5 se ambas as fontes falharem.

## Pacote / Módulo
- **Novo:** `app/analyzers/trend_analyzer.py`
- **Modificado:** `app/scoring/scorer.py` — `score_product()` aceita `trend_score: float = 0.5`
- **Modificado:** `app/pipeline.py` — chama `compute_trend_score()` antes de `score_product()`
- **Modificado:** `requirements.txt` — adicionar `pytrends`

## Contratos

```python
# app/analyzers/trend_analyzer.py

from dataclasses import dataclass

@dataclass
class TrendSignal:
    title: str
    sales_volume: str  # raw string from 1688 (e.g. "1234+")

async def fetch_1688_trending(category_keyword: str) -> list[TrendSignal]:
    """Scrape 1688.com bestsellers via Firecrawl /v1/scrape. Returns [] on failure."""

def fetch_google_trends_br(keywords: list[str]) -> dict[str, float]:
    """Return normalized 0-1 average interest for last 90 days, geo=BR.
    Returns {} on failure (rate limit, empty result, etc.)."""

def _extract_keyword(product_title: str) -> str:
    """Return first 3 words of title as keyword string."""

def compute_trend_score(product_title: str) -> float:
    """Return 0.0-1.0 trend score using cache. Falls back to 0.5 if all sources fail."""
```

```python
# app/scoring/scorer.py — assinatura modificada
def score_product(ali: AliProduct, market: BRMarket, cost: ImportCost, trend_score: float = 0.5) -> ProductScore:
    ...
    score_tendencia = trend_score  # replaces hardcoded 0.5
```

## Detalhes de Implementação

- **1688.com**: `GET https://www.1688.com/page/search_product.html?keywords={keyword}` via Firecrawl `/v1/scrape` com `formats: ["extract"]` e schema `{title: string, sales: string}`
- **pytrends**: `TrendReq(hl='pt-BR', geo='BR').build_payload([keyword], timeframe='today 3-m')` → `interest_over_time()` → média dos últimos 90 dias / 100 → float 0-1
- **Cache**: dict em memória (module-level) `_trend_cache: dict[str, tuple[float, datetime]]` — TTL via env `TREND_CACHE_TTL_HOURS` (default 24)
- **Keyword extraction**: `" ".join(title.split()[:3])`
- **Retry pytrends**: 3 tentativas, backoff exponencial 2^n segundos (max 8s)
- **Fallback chain**: Google Trends score → se falhar → 0.5. 1688 usado apenas para descoberta de keywords, não score direto.
- **Score combinado**: `0.6 * google_trends_score + 0.4 * 0.5 (base)` quando só Google Trends disponível; `0.5` se tudo falhar.

## Tasks
- [x] Escrever spec (TASK-128)
- [x] RED: escrever tests/test_issue128_trend_analyzer.py (falham)
- [x] Adicionar pytrends a requirements.txt
- [x] GREEN: implementar app/analyzers/trend_analyzer.py
- [x] GREEN: modificar app/scoring/scorer.py (trend_score param)
- [x] GREEN: modificar app/pipeline.py (chama compute_trend_score)
- [x] REFACTOR: retry backoff, limpeza, datetime timezone-aware
- [x] VERIFY: pytest tests/ -x -q → 264 passed

## Critérios de Verificação (da issue)
```bash
test -f app/analyzers/trend_analyzer.py && echo "PASS" || echo "FAIL"
python3 -c "import pytrends; print('PASS')" 2>/dev/null || echo "FAIL: pytrends ausente"
grep -n "score_tendencia.*0\.5" app/pipeline.py && echo "WARN: ainda hardcoded" || echo "PASS: substituído"
pytest tests/ -x -q
```
