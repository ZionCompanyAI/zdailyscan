# [TASK-137] fix: filtrar produtos não-tech do scan de categorias

## Objetivo
Scan de categorias AliExpress retorna produtos mistos (fashion, vestuário, etc).
Adicionar filtro que identifica produtos non-tech pelo título e os exclui como viáveis.
Scan de keywords NÃO é afetado (já retorna 100% tech).

## Pacote / Módulo
`app/pipeline.py` — função `run_daily_scan()`

## Contratos

```python
TECH_KEYWORDS: list[str]  # lista de termos que caracterizam produto tech

def is_tech_product(title: str) -> bool:
    """Retorna True se o título contém ao menos um keyword tech (case-insensitive)."""
```

### Comportamento no pipeline
- Para produtos oriundos de scan de **categoria** (`keyword == ""`):
  - Se `is_tech_product(product.title)` → `False`:
    - Criar `ProductScore(viavel=False, score_total=0.0, ...)` sem chamar APIs externas
    - Adicionar a `all_scores` (conta em `total_scanned`) e `continue`
- Para produtos oriundos de scan de **keyword** (`keyword != ""`):
  - Nenhuma mudança — comportamento atual mantido

## Detalhes de Implementação
- `TECH_KEYWORDS` e `is_tech_product()` definidos em `app/pipeline.py`
- Keywords conforme spec da issue: usb, hdmi, hub, adapter, charger, cable, bluetooth,
  wifi, laptop, phone, iphone, android, thunderbolt, display, port, wireless, earphone,
  headphone, speaker, power bank, screen, monitor, keyboard, mouse, ssd, memory, ram,
  type-c, type c, lightning, ethernet, converter, splitter, docking, stand, mount
- Verificação case-insensitive: `title.lower()`

## Tasks
- [x] Criar `TECH_KEYWORDS` e `is_tech_product()` em pipeline.py
- [x] Aplicar filtro no loop de produtos de categoria em `run_daily_scan()`
- [x] Escrever testes unitários em `tests/test_issue137_tech_filter.py`

## Critérios de Verificação
- `is_tech_product("USB-C Hub 7-in-1")` → `True`
- `is_tech_product("HDMI Adapter 4K")` → `True`
- `is_tech_product("Men Fashion Quick Dry Pants")` → `False`
- `is_tech_product("Summer Women Thin Sunscreen Cardigan")` → `False`
- Pipeline: produto fashion de categoria → `viavel=False`, `score_total=0.0`
- Pipeline: produto tech de categoria → scoring normal
- Pipeline: produto fashion de **keyword** scan → scoring normal (sem filtro)
