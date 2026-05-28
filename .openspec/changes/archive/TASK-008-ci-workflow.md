# [TASK-008] CI GitHub Actions — merge queue + ruff + pytest

## Objetivo
Criar `.github/workflows/ci.yml` habilitando CI para PRs e GitHub Merge Queue,
com instalação correta de todas as dependências (requirements.txt + extras dev).

## Pacote / Módulo
`.github/workflows/ci.yml` — arquivo novo de workflow GitHub Actions.

## Contratos (Referências Técnicas)

```yaml
# Triggers obrigatórios
on:
  pull_request:
    branches: [main]
  merge_group:

# Steps obrigatórios (ordem importa)
- pip install -r requirements.txt        # PRIMEIRO (crawl4ai e deps)
- pip install -e ".[dev]" ruff           # SEGUNDO (extras + ferramentas)
- ruff check .                           # lint
- pytest tests/ -x                       # testes
```

## Critérios de Verificação (Acceptance Criteria)

```bash
test -f .github/workflows/ci.yml
grep -q "requirements.txt" .github/workflows/ci.yml
grep -q "merge_group" .github/workflows/ci.yml
grep -q "pytest" .github/workflows/ci.yml
grep -q "ruff" .github/workflows/ci.yml
```

## Tasks

- [x] Criar diretório `.github/workflows/`
- [x] Criar `.github/workflows/ci.yml` com conteúdo exato da spec
- [x] Validar todos os acceptance criteria
