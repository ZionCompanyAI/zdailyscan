# [TASK-008] Habilitar GitHub Merge Queue via CI Workflow

## Objetivo
Criar `.github/workflows/ci.yml` com status checks obrigatórios (pytest + ruff) e trigger
`merge_group`, permitindo que o GitHub Merge Queue teste PRs em sequência antes do merge —
eliminando rebase conflicts entre agentes AutoDevSr paralelos.

## Pacote / Módulo
`.github/workflows/ci.yml` — novo arquivo de infra, sem mudanças em código Python.

## Contratos (Referências Técnicas)

```yaml
# .github/workflows/ci.yml — estrutura esperada
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  merge_group:          # trigger obrigatório para Merge Queue

jobs:
  ci:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e ".[dev]" ruff
      - run: ruff check .
      - run: pytest tests/ -x
```

## Detalhes de Implementação
- Python version: 3.11 (alinhado com `requires-python = ">=3.11"` do pyproject.toml)
- Cache pip via `actions/setup-python` com `cache: 'pip'`
- Branch protection via GitHub API (gh CLI) após criação do workflow:
  - `required_status_checks` apontando para o job `ci`
  - `merge_queue_enabled: true`

## Tasks
- [x] Criar `.github/workflows/ci.yml`
- [x] Configurar branch protection via GitHub API

## Critérios de Verificação
```bash
test -f .github/workflows/ci.yml
grep -q "pytest" .github/workflows/ci.yml
grep -q "ruff" .github/workflows/ci.yml
grep -q "merge_group" .github/workflows/ci.yml
```
