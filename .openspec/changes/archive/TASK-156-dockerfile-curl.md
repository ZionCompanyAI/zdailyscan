# [TASK-156] fix(Dockerfile): instalar curl — subprocess.run falha com FileNotFoundError

## Objetivo
Adicionar `curl` à imagem Docker para que `subprocess.run(["curl", ...])` no scraper
(introduzido no PR #155) funcione sem `FileNotFoundError`.

## Pacote / Módulo
`Dockerfile` — linha após `FROM python:3.11-slim`.

## Contratos

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
```

## Detalhes de Implementação
- `python:3.11-slim` não inclui `curl` por padrão.
- `--no-install-recommends` minimiza tamanho da imagem.
- `rm -rf /var/lib/apt/lists/*` limpa cache apt após instalação.

## Tasks
- [x] Adicionar linha `RUN apt-get install curl` após FROM no Dockerfile

## Critérios de Verificação
```bash
grep -q "apt-get install.*curl" Dockerfile
```

## Verificação
✅ `grep -q "apt-get install.*curl" Dockerfile` — passou (commit e6b1c65)

## Implementado em
commit `e6b1c65` — fix(Dockerfile): instalar curl para subprocess.run no scraper (#156)
