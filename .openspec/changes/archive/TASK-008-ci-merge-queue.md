# [TASK-008] CI GitHub Actions + Merge Queue

## Objetivo
Criar `.github/workflows/ci.yml` com CI funcional que executa lint (ruff) e testes (pytest)
em pull_request e merge_group, excluindo crawl4ai do install (requer Playwright — não disponível em CI).

## Pacote / Módulo
`.github/workflows/ci.yml` (arquivo novo)

## Contratos (Referências Técnicas)

```yaml
# Triggers obrigatórios
on:
  pull_request:
    branches: [main]
  merge_group:

# Steps obrigatórios
- grep -v crawl4ai requirements.txt | pip install -r /dev/stdin
- pip install -e ".[dev]" ruff
- ruff check .
- pytest tests/ -x
```

## Detalhes de Implementação
- Python 3.11, ubuntu-latest
- Excluir crawl4ai via `grep -v crawl4ai` — requer Playwright, não disponível em CI
- O código já tem `try/except ImportError` para crawl4ai — mocks automáticos no test suite

## Tasks

- [x] Criar `.github/workflows/` directory
- [x] Criar `ci.yml` com conteúdo exato da spec
- [x] Verificar acceptance criteria (5 bash checks)

## Critérios de Verificação

```bash
test -f .github/workflows/ci.yml
grep -q "merge_group" .github/workflows/ci.yml
grep -q "grep -v crawl4ai" .github/workflows/ci.yml
grep -q "pytest" .github/workflows/ci.yml
grep -q "ruff" .github/workflows/ci.yml
```
