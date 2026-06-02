# [TASK-154] fix(scraper): subprocess curl + corrigir undefined-como-chave JSON

## Objetivo
Resolver dois problemas identificados nos logs do deploy 5bdc2338:
1. `undefined` como CHAVE JSON: `re.sub(r"\bundefined\b", "null", raw)` converte `{ undefined: {...} }` → `{ null: {...} }` — JSON inválido (chave deve ser string entre aspas). Fix: regex em 2 passos.
2. Rate limiting (thin pages): httpx fingerprint bloqueado após 1º request → substituir por `subprocess curl --compressed` (fingerprint diferente).

## Pacote / Módulo
`app/scrapers/aliexpress.py` → função `_scrape_with_scrapling()`
`nixpacks.toml` → criar na raiz se não existir

## Contratos (Referências Técnicas)

```python
# Passo 1 — undefined como CHAVE (antes do passo 2)
raw = re.sub(r'(?<=[{,\[]\s{0,5})undefined(?=\s*:)', '"_undefined_"', raw)
# Passo 2 — undefined como VALOR/restante
raw = re.sub(r'\bundefined\b', 'null', raw)

# subprocess curl
result = _subprocess.run(
    ["curl", "-s", "-L", "--max-time", "20", "--compressed",
     "-H", f"User-Agent: {_SCRAPLING_HEADERS['User-Agent']}",
     "-H", f"Accept: {_SCRAPLING_HEADERS['Accept']}",
     "-H", "Accept-Language: en-US,en;q=0.9",
     "-H", "Accept-Encoding: gzip, deflate, br",
     url],
    capture_output=True, timeout=25
)
html = result.stdout.decode("utf-8", errors="replace") if result.returncode == 0 else ""
```

## Detalhes de Implementação
- Remover `import httpx` da função `_scrape_with_scrapling` (httpx permanece em outros lugares)
- Adicionar `import subprocess as _subprocess` dentro da função
- Substituir bloco `try: resp = httpx.get(...)` pelo bloco subprocess curl
- Substituir a linha de re.sub undefined pelas 2 linhas novas
- Criar `nixpacks.toml` na raiz com `nixPkgs = ["curl"]`

## Tasks
- [x] Criar spec TASK-154
- [x] RED: escrever testes que falham
- [x] GREEN: implementar mudanças
- [x] REFACTOR: limpar + verificar suite completa (310 passed)
- [x] Archive

## Critérios de Verificação
- `subprocess.run` chamado com `["curl", ..., "--compressed", ...]`
- `httpx.get` NÃO chamado dentro de `_scrape_with_scrapling`
- `{ undefined: {...} }` parseado corretamente com chave `"_undefined_"`
- `undefined` como valor ainda vira `null`
- `nixpacks.toml` existe com `nixPkgs = ["curl"]`
- Suite completa de testes passa
