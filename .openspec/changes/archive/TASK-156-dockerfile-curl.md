# [TASK-156] fix(Dockerfile): instalar curl — subprocess.run falha com FileNotFoundError

## Objetivo
Instalar `curl` na imagem Docker para que `subprocess.run(["curl", ...])` do scraper Scrapling funcione sem lançar `FileNotFoundError(2, No such file or directory)`.

## Pacote / Módulo
`Dockerfile` — linha imediatamente após `FROM python:3.11-slim`.

## Contratos (Referências Técnicas)

```dockerfile
FROM python:3.11-slim

# NOVO — linha a adicionar:
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
...
```

## Detalhes de Implementação
- `--no-install-recommends` mantém a imagem enxuta
- `rm -rf /var/lib/apt/lists/*` limpa cache apt reduzindo tamanho da camada
- Nenhum outro arquivo precisa ser alterado

## Tasks (checklist de execução)
- [x] Adicionar linha RUN apt-get no Dockerfile

## Critérios de Verificação
- Dockerfile contém a linha `RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*`
- Suite de testes passa (`pytest tests/ -x`)

## RED (evidence)
```
[scraper:scrapling] attempt=0 curl failed: FileNotFoundError(2, No such file or directory)
```
Erro de runtime confirmado — curl ausente na imagem `python:3.11-slim`. Testes unitários mocam subprocess.run (sem necessidade de teste novo para esta mudança de infra).
