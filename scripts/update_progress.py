"""Sincroniza .openspec/progress.md com o estado real de .openspec/changes/."""
from pathlib import Path

OPENSPEC_DIR = Path(".openspec")
CHANGES_DIR = OPENSPEC_DIR / "changes"
PROGRESS_FILE = OPENSPEC_DIR / "progress.md"


def read_task_title(filepath: Path) -> str:
    """Extrai título do primeiro header # de um spec file. Retorna filepath.stem se não achar."""
    for line in filepath.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return filepath.stem


def collect_tasks(changes_dir: Path) -> tuple[list[Path], list[Path]]:
    """Retorna (in_progress, completed): *.md em changes_dir (não archive) e changes_dir/archive/."""
    archive_dir = changes_dir / "archive"

    in_progress: list[Path] = []
    if changes_dir.exists():
        in_progress = sorted(p for p in changes_dir.glob("*.md"))

    completed: list[Path] = []
    if archive_dir.exists():
        completed = sorted(p for p in archive_dir.glob("*.md"))

    return in_progress, completed


def render_progress(in_progress: list[Path], completed: list[Path]) -> str:
    """Retorna string completa do progress.md no formato padrão .openspec."""
    lines = ["# Progress", "", "## Em andamento"]
    if in_progress:
        for f in in_progress:
            title = read_task_title(f)
            lines.append(f"- {f.stem}: {title}")
    else:
        lines.append("(nenhum)")

    lines.append("")
    lines.append("## Concluído")
    if completed:
        for f in completed:
            title = read_task_title(f)
            lines.append(f"- {f.stem}: {title}")
    else:
        lines.append("(nenhum)")

    return "\n".join(lines) + "\n"


def main() -> None:
    in_progress, completed = collect_tasks(CHANGES_DIR)
    content = render_progress(in_progress, completed)
    PROGRESS_FILE.write_text(content, encoding="utf-8")
    print(f"progress.md atualizado: {len(in_progress)} em andamento, {len(completed)} concluídos")


if __name__ == "__main__":
    main()
