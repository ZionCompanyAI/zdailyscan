# [TASK-012] CI workflow — habilitar GitHub Merge Queue

## Objetivo
Criar `.github/workflows/ci.yml` com CI funcional que suporte Merge Queue.

## Contratos
- Trigger: `pull_request` em `main` + `merge_group`
- Jobs: lint (ruff) + test (pytest -x)
- Fix setuptools: `pip install --upgrade pip setuptools` antes de instalar deps
- Fix crawl4ai: `grep -v crawl4ai requirements.txt | pip install -r /dev/stdin`

## Tasks
- [x] Criar/atualizar `.github/workflows/ci.yml` com conteúdo exato da spec
- [x] Verificar 5 critérios de aceite (todos PASS)

## Resultado
Arquivo criado com todos os critérios de aceite satisfeitos.
