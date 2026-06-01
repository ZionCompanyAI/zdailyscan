# [TASK-137] fix: filtrar produtos não-tech do scan de categorias

## Objetivo
Produtos de moda/vestuário que aparecem em páginas de categorias mistas do AliExpress
devem ser marcados como não viáveis antes de entrar no relatório, sem afetar produtos tech.

## Pacote / Módulo
`app/pipeline.py` — adicionar `TECH_KEYWORDS` e `is_tech_product()`, aplicar no loop do scan.

## Contratos

```python
TECH_KEYWORDS: list[str]  # lista de substrings tech em lowercase

def is_tech_product(title: str) -> bool:
    """Retorna True se o título contiver pelo menos uma keyword tech."""
```

Aplicação no pipeline (após `score = score_product(...)`):
```python
if not is_tech_product(product.title):
    score.viavel = False
    score.score_total = 0.0
```

## Detalhes de Implementação
- Keywords da issue (34 termos): usb, hdmi, hub, adapter, charger, cable, bluetooth, wifi,
  laptop, phone, iphone, android, thunderbolt, display, port, wireless, earphone, headphone,
  speaker, power bank, screen, monitor, keyboard, mouse, ssd, memory, ram, type-c, type c,
  lightning, ethernet, converter, splitter, docking, stand, mount
- Comparação case-insensitive via `title.lower()`
- Produto não-tech: viavel=False e score_total=0.0 (conta em total_scanned, não em total_viable)
- Produtos de keywords (keyword scan) também passam pelo filtro — consistência

## Tasks
- [x] Escrever testes RED (test_issue137_tech_filter.py)
- [x] Implementar TECH_KEYWORDS + is_tech_product em pipeline.py
- [x] Aplicar filtro no loop do scan
- [x] Verificar suite completa

## Critérios de Verificação
- `is_tech_product("USB Hub 3.0")` → True
- `is_tech_product("Men Fashion Quick Dry Pants")` → False
- Pipeline com produtos fashion → total_viable=0
- Pipeline com produtos tech → continua viável
