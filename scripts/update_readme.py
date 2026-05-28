"""Re-gera a seção ## Módulos do README.md com base nos arquivos app/**/*.py."""
import ast
from pathlib import Path

README = Path("README.md")
APP_DIR = Path("app")


def get_module_docstring(filepath: Path) -> str:
    """Extrai docstring de nível de módulo via ast.parse. Retorna "" se ausente ou erro."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
        raw = ast.get_docstring(tree) or ""
        return raw.splitlines()[0] if raw else ""
    except Exception:
        return ""


def collect_modules(app_dir: Path) -> list[tuple[str, str]]:
    """Retorna lista de (relative_path_str, description) para cada .py não-__init__ em app_dir."""
    modules: list[tuple[str, str]] = []
    for filepath in sorted(app_dir.rglob("*.py")):
        if filepath.name == "__init__.py":
            continue
        try:
            relative = str(filepath.relative_to(Path(".")))
        except ValueError:
            relative = str(filepath)
        desc = get_module_docstring(filepath)
        if not desc:
            desc = f"`{relative}` — (sem docstring)"
        modules.append((relative, desc))
    return modules


def build_modules_table(modules: list[tuple[str, str]]) -> list[str]:
    """Retorna linhas markdown da tabela ## Módulos."""
    lines = ["## Módulos", "", "| Módulo | Descrição |", "|--------|-----------|"]
    for path, desc in modules:
        lines.append(f"| `{path}` | {desc} |")
    return lines


def replace_modules_section(content: str, modules: list[tuple[str, str]]) -> str:
    """Substitui seção ## Módulos em content; insere ao fim se ausente. Retorna novo content."""
    lines = content.splitlines()

    start_idx: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == "## Módulos":
            start_idx = i
            break

    new_section = build_modules_table(modules)

    if start_idx is None:
        # Append at end
        new_lines = lines + [""] + new_section
        return "\n".join(new_lines) + "\n"

    # Find end of section (next ## heading or EOF)
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if lines[i].startswith("## "):
            end_idx = i
            break

    # Preserve trailing blank line before next section
    new_lines = lines[:start_idx] + new_section + [""] + lines[end_idx:]
    return "\n".join(new_lines) + "\n"


def main() -> None:
    content = README.read_text(encoding="utf-8")
    modules = collect_modules(APP_DIR)
    updated = replace_modules_section(content, modules)
    README.write_text(updated, encoding="utf-8")
    print(f"README.md atualizado: {len(modules)} módulos encontrados")


if __name__ == "__main__":
    main()
