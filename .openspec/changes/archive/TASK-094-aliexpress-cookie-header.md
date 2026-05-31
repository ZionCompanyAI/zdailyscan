# [TASK-094] Cookie header + aliexpress.us URL for Firecrawl scraper

## Objetivo
Passar cookies de sessão do AliExpress via header `Cookie` no request Firecrawl,
e usar `aliexpress.us` em vez de `aliexpress.com` como URL alvo do scrape.

## Pacote / Módulo
`app/scrapers/fallback_firecrawl.py` — função `get_products_via_firecrawl()`

## Contratos

```python
# Env var esperada:
# ALIEXPRESS_SESSION_COOKIES = JSON array de {name, value, ...}
# Ex: [{"name": "xman_us_f", "value": "xxx"}, {"name": "_tbtoken", "value": "yyy"}]

# URL alvo (antes): https://www.aliexpress.com/category/{id}/bestselling.html
# URL alvo (depois): https://www.aliexpress.us/category/{id}/bestselling.html

# Header injetado quando env var presente e parsável:
# headers["Cookie"] = "xman_us_f=xxx; _tbtoken=yyy"
```

## Detalhes de Implementação
- Ler `ALIEXPRESS_SESSION_COOKIES` via `os.environ.get()`
- Parsear como JSON array; cada item tem `"name"` e `"value"`
- Montar string `"name1=val1; name2=val2"` filtrando itens sem `value`
- Injetar no `headers` dict (já construído para o Bearer token)
- Silenciar qualquer `Exception` no parse (env var malformada não deve quebrar o scraper)
- Alterar domínio de `aliexpress.com` para `aliexpress.us`

## Tasks
- [x] Escrever testes (RED)
- [x] Implementar (GREEN)
- [x] Refactor + verify (REFACTOR)
- [x] Archive

## Critérios de Verificação
```bash
grep -q ALIEXPRESS_SESSION_COOKIES app/scrapers/fallback_firecrawl.py
grep -q aliexpress.us app/scrapers/fallback_firecrawl.py
```
