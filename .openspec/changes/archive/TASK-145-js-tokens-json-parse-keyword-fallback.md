# [TASK-145] fix(scraper) — JS undefined/NaN sanitization + keyword multi-pattern fallback

## Objetivo

Dois bugs em `_scrape_with_scrapling` causam retorno vazio:

1. **JSON parse falha para categorias** — `window._dida_config_._init_data_` pode conter tokens
   JavaScript (`undefined`, `NaN`, `Infinity`) inválidos em JSON. O `raw_decode` atual opera
   diretamente no HTML com offset, sem pré-processar o texto extraído.

2. **Keyword search não encontra _init_data_** — URL `wholesale?SearchText=...` usa
   `window.runParams` em vez de `window._dida_config_._init_data_`. Sem fallback de padrão,
   sempre retorna `[]`.

## Pacote / Módulo

`app/scrapers/aliexpress.py` → função `_scrape_with_scrapling()`

## Contratos

```python
# Após o fix, _scrape_with_scrapling deve:
# 1. Pré-processar o texto extraído substituindo tokens JS antes do JSON parse
# 2. Tentar múltiplos padrões de variável JS quando _init_data_ não for encontrado

_JS_PATTERNS = [
    r"window\._dida_config_\._init_data_\s*=\s*",
    r"window\.runParams\s*=\s*",
    r"window\.__INITIAL_STATE__\s*=\s*",
]

# Substituições antes de raw_decode:
# raw = html[m.end():]
# raw = re.sub(r"\bundefined\b", "null", raw)
# raw = re.sub(r"\bNaN\b", "null", raw)
# raw = re.sub(r"\bInfinity\b", "null", raw)
# data, _ = json.JSONDecoder().raw_decode(raw)
```

## Tasks

- [x] Criar `.openspec/changes/TASK-145-...md`
- [x] RED: escrever `tests/test_issue145_js_tokens_keyword_fallback.py` — FAIL confirmado
- [x] GREEN: implementar pré-processamento de tokens JS + multi-pattern em `_scrape_with_scrapling`
- [x] REFACTOR: limpar, confirmar testes verdes
- [x] Archive

## Critérios de Verificação

- `test_scrapling_undefined_nan_in_html` → produtos extraídos mesmo com `undefined`/`NaN` no JSON
- `test_scrapling_nan_deep_in_json` → falha de parse profundo (~177k chars) não ocorre
- `test_scrapling_keyword_uses_runparams_fallback` → keyword search funciona com `window.runParams`
- `test_scrapling_keyword_init_data_takes_priority` → `_init_data_` tem prioridade sobre `runParams`
- CI verde (pytest sem falhas)
