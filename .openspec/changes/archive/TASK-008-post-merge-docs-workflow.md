# [TASK-008] Post-merge GitHub Action — auto-atualiza README e progress.md

## Objetivo
Criar workflow GitHub Actions que dispara no push em `main` e atualiza automaticamente
`.openspec/progress.md` (lista de tasks concluídas vs em andamento) e a seção `## Módulos`
do `README.md` com os módulos reais do diretório `app/`.

## Pacote / Módulo
- `.github/workflows/post-merge-docs.yml` — workflow GHA
- `scripts/update_progress.py` — sincroniza `.openspec/progress.md` com estado real do `.openspec/changes/`
- `scripts/update_readme.py` — re-gera tabela `## Módulos` no README baseada nos arquivos `app/**/*.py`

## Contratos

```python
# scripts/update_progress.py — funções testáveis
def read_task_title(filepath: Path) -> str:
    """Extrai título do primeiro header # de um spec file. Retorna filepath.stem se não achar."""

def collect_tasks(changes_dir: Path) -> tuple[list[Path], list[Path]]:
    """Retorna (in_progress, completed): *.md em changes_dir (não archive) e changes_dir/archive/."""

def render_progress(in_progress: list[Path], completed: list[Path]) -> str:
    """Retorna string completa do progress.md no formato padrão .openspec."""

def main() -> None:
    """Entry point: coleta tasks, renderiza e escreve .openspec/progress.md."""
```

```python
# scripts/update_readme.py — funções testáveis
def get_module_docstring(filepath: Path) -> str:
    """Extrai docstring de nível de módulo via ast.parse. Retorna "" se ausente ou erro."""

def collect_modules(app_dir: Path) -> list[tuple[str, str]]:
    """Retorna lista de (relative_path_str, description) para cada .py não-__init__ em app_dir."""

def build_modules_table(modules: list[tuple[str, str]]) -> list[str]:
    """Retorna linhas markdown da tabela ## Módulos."""

def replace_modules_section(content: str, modules: list[tuple[str, str]]) -> str:
    """Substitui seção ## Módulos em content; insere ao fim se ausente. Retorna novo content."""

def main() -> None:
    """Entry point: coleta módulos, lê README.md, substitui seção, escreve README.md."""
```

## Tasks

- [x] Criar `scripts/update_progress.py` com funções `read_task_title`, `collect_tasks`, `render_progress`, `main`
- [x] Criar `scripts/update_readme.py` com funções `get_module_docstring`, `collect_modules`, `build_modules_table`, `replace_modules_section`, `main`
- [x] Criar `.github/workflows/post-merge-docs.yml`
- [x] Escrever `tests/test_update_scripts.py` (RED antes do código)

## Critérios de Verificação
```bash
ls .github/workflows/post-merge-docs.yml
ls scripts/update_progress.py
ls scripts/update_readme.py
pytest tests/test_update_scripts.py -v
```
