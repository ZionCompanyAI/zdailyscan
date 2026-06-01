# [TASK-129] chore: remover categorias não-tech do scanner

## Objetivo
Atualizar as categorias padrão do scanner para focar exclusivamente no nicho tech da Loja HI Select, removendo Casa & Jardim (200000828) e Esportes (200000834).

## Pacote / Módulo
- `app/pipeline.py` → constante `CATEGORIES`
- `app/routers/dashboard.py` → dict `CATEGORY_NAMES`
- `tests/test_issue42_settings_categories.py` → testes que assumem 5 categorias

## Contratos (Referências Técnicas)

```python
# app/pipeline.py — DEPOIS
CATEGORIES: list[str] = [
    "200003655",  # Consumer Electronics
    "100003070",  # Phones & Telecommunications
    "200000783",  # Computer & Office
]

# app/routers/dashboard.py — DEPOIS
CATEGORY_NAMES: dict[str, str] = {
    "200003655": "Consumer Electronics",
    "100003070": "Phones & Telecom",
    "200000783": "Computer & Office",
}
```

## Detalhes de Implementação
- Remoção pura de linhas — sem lógica nova
- `get_active_categories()` não muda (filtra dinamicamente contra `CATEGORIES`)
- Testes que verificam quantidade ou presença das 2 categorias removidas devem ser atualizados

## Tasks
- [x] Atualizar testes (RED: falham com implementação atual)
- [x] Remover entradas de `CATEGORIES` em `app/pipeline.py`
- [x] Remover entradas de `CATEGORY_NAMES` em `app/routers/dashboard.py`
- [x] Verificar suite completa verde

## Critérios de Verificação
```bash
grep -q "200000828\|200000834" app/pipeline.py && echo "FAIL" || echo "PASS"
grep -q "200000828\|200000834" app/routers/dashboard.py && echo "FAIL" || echo "PASS"
pytest tests/ -x -q
```
