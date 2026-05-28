# [TASK-006] Conectar scraper Crawl4AI ao pipeline e expor endpoint

## Objetivo
PR #17 mergeou `app/scrapers/` com Crawl4AI, mas pipeline.py ainda importa
o scraper legado `app.aliexpress`. Conectar o novo scraper ao pipeline e
expor endpoint REST `/scrapers/aliexpress`.

## Pacote / Módulo
- `app/scrapers/__init__.py` → exportar `get_hot_products`
- `app/pipeline.py` linha 6 → trocar import
- `app/main.py` → adicionar endpoint `GET /scrapers/aliexpress`

## Contratos

```python
# app/scrapers/__init__.py
from app.scrapers.aliexpress import get_hot_products  # re-export

# app/pipeline.py linha 6 (único change)
from app.scrapers import get_hot_products  # era: from app.aliexpress import get_hot_products

# app/main.py — novo endpoint
@app.get("/scrapers/aliexpress")
async def scrape_aliexpress(category: str = "200003655", limit: int = 20):
    products = await get_hot_products(category_id=category, max_results=limit)
    return {"products": [p.dict() for p in products], "count": len(products)}
```

## Acceptance Criteria (bash)
```bash
grep -n "from app.scrapers import get_hot_products" app/pipeline.py
grep -n "scrapers/aliexpress" app/main.py
! grep "from app.aliexpress" app/pipeline.py
```

## Tasks
- [ ] app/scrapers/__init__.py — re-exportar get_hot_products
- [ ] app/pipeline.py — trocar import linha 6
- [ ] app/main.py — adicionar endpoint GET /scrapers/aliexpress
- [ ] Escrever testes RED (falham antes do fix)
- [ ] GREEN — implementar mínimo para passar
- [ ] VERIFY suite completa

## O que NÃO fazer
- NÃO reimplementar o scraper
- NÃO criar app/models.py
- NÃO remover endpoints existentes
