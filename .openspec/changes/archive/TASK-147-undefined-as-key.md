# [TASK-147] fix(scraper) — undefined como CHAVE quebra JSON parse

## Objetivo
Quando `_init_data_` começa com `{ undefined: {...} }`, o re.sub atual converte para
`{ null: {...} }` — chave sem aspas, JSON inválido. Corrigir sanitização para distinguir
`undefined` como chave (→ `"undefined"`) de `undefined` como valor (→ `null`).

## Pacote / Módulo
`app/scrapers/aliexpress.py` → função `_scrape_with_scrapling()`, linha 420

## Contratos (Referências Técnicas)

```python
# ANTES (bugado — substitui undefined por null em qualquer posição):
raw = re.sub(r"\bundefined\b", "null", raw)

# DEPOIS (correto — 4 padrões específicos, em ordem):
raw = re.sub(r'\bundefined\b(\s*:)', r'"undefined"\1', raw)  # key: {undefined: x}
raw = re.sub(r':\s*\bundefined\b', ': null', raw)             # value: {"k": undefined}
raw = re.sub(r':\s*\bNaN\b', ': null', raw)                   # value: {"k": NaN}
raw = re.sub(r':\s*\bInfinity\b', ': null', raw)              # value: {"k": Infinity}
```

## Critérios de Verificação
- `undefined` como CHAVE: `{ undefined: {...} }` → parse bem-sucedido, products retornados
- `undefined` como VALOR: `{"k": undefined}` → parse bem-sucedido
- `NaN` como VALOR → parse bem-sucedido
- `{ undefined: {"k": undefined} }` → parse bem-sucedido (ambos os casos num único doc)
- Todos os testes de `test_issue145_js_tokens_keyword_fallback.py` continuam verdes

## Tasks
- [x] Criar spec TASK-147
- [x] RED — escrever `tests/test_issue147_undefined_key.py` (deve falhar)
- [x] GREEN — substituir re.sub em `_scrape_with_scrapling`
- [x] REFACTOR — linter, verificar suite completa
- [x] Archive
