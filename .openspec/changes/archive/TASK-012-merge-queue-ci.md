---
name: TASK-012-merge-queue-ci
description: Criar CI workflow GitHub Actions com merge_group trigger, pytest e ruff
type: project
---

# [TASK-012] GitHub Merge Queue — CI Workflow

## Objetivo
Criar `.github/workflows/ci.yml` que habilita GitHub Merge Queue para eliminar
rebase conflicts entre PRs paralelos de agentes AutoDevSr.

## Pacote / Módulo
`.github/workflows/ci.yml` — novo arquivo

## Contratos (Referências Técnicas)

```yaml
# Triggers obrigatórios
on:
  pull_request:
  merge_group:

# Steps obrigatórios
- uses: actions/checkout@v4
- name: Set up Python
- name: Install deps
- name: ruff check
- name: pytest
```

## Detalhes de Implementação
- Python 3.11 (conforme pyproject.toml `requires-python = ">=3.11"`)
- Instalar dev deps: `pip install pytest pytest-asyncio anyio ruff`
- ruff check sem modificações (`--no-fix`)
- pytest em `tests/` com `-x` (fail fast)
- Trigger `merge_group` é o que habilita Merge Queue no GitHub

## Tasks (checklist de execução)
- [x] Spec criada
- [ ] Tests RED criados e falhando
- [ ] `.github/workflows/ci.yml` criado (GREEN)
- [ ] Verificação REFACTOR + acceptance criteria

## Critérios de Verificação (Acceptance Criteria)
```bash
test -f .github/workflows/ci.yml
grep -q "pytest" .github/workflows/ci.yml
grep -q "ruff" .github/workflows/ci.yml
grep -q "merge_group" .github/workflows/ci.yml
```
