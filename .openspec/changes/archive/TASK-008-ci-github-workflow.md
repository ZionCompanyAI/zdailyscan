# [TASK-008] CI GitHub Actions — Merge Queue

## Objetivo
Criar `.github/workflows/ci.yml` para habilitar GitHub Merge Queue e CI automático em PRs.

## Pacote / Módulo
`.github/workflows/ci.yml` — novo arquivo de workflow GitHub Actions.

## Contratos (Referências Técnicas)
Arquivo YAML exato a criar:

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  merge_group:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: |
          pip install --upgrade pip setuptools
          grep -v crawl4ai requirements.txt | pip install -r /dev/stdin
          pip install -e ".[dev]" ruff

      - name: Lint
        run: ruff check .

      - name: Test
        run: pytest tests/ -x
```

## Acceptance Criteria (bash)
```bash
test -f .github/workflows/ci.yml
grep -q "upgrade pip setuptools" .github/workflows/ci.yml
grep -q "grep -v crawl4ai" .github/workflows/ci.yml
grep -q "merge_group" .github/workflows/ci.yml
grep -q "pytest" .github/workflows/ci.yml && grep -q "ruff" .github/workflows/ci.yml
```

## Tasks
- [ ] Criar diretório `.github/workflows/`
- [ ] Criar arquivo `ci.yml` com conteúdo exato
- [ ] Verificar acceptance criteria

## Status
Spec aprovada via issue #12 (corpo da issue = spec completa).
