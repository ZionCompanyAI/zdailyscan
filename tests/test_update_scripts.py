"""Tests for scripts/update_progress.py and scripts/update_readme.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import update_progress
import update_readme


# ---------------------------------------------------------------------------
# update_progress
# ---------------------------------------------------------------------------


class TestReadTaskTitle:
    def test_extracts_first_h1(self, tmp_path):
        f = tmp_path / "TASK-001-foo.md"
        f.write_text("# [TASK-001] My Title\n\nsome body\n")
        assert update_progress.read_task_title(f) == "[TASK-001] My Title"

    def test_returns_stem_when_no_h1(self, tmp_path):
        f = tmp_path / "TASK-002-bar.md"
        f.write_text("## Not a h1\n\nbody\n")
        assert update_progress.read_task_title(f) == "TASK-002-bar"

    def test_ignores_h2_and_below(self, tmp_path):
        f = tmp_path / "TASK-003-baz.md"
        f.write_text("## Section\n# [TASK-003] Real Title\n")
        assert update_progress.read_task_title(f) == "[TASK-003] Real Title"


class TestCollectTasks:
    def test_empty_dir_returns_empty_lists(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        (changes / "archive").mkdir()
        in_prog, done = update_progress.collect_tasks(changes)
        assert in_prog == []
        assert done == []

    def test_detects_in_progress_tasks(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        (changes / "archive").mkdir()
        (changes / "TASK-001-foo.md").write_text("# T1\n")
        (changes / "TASK-002-bar.md").write_text("# T2\n")
        in_prog, done = update_progress.collect_tasks(changes)
        assert len(in_prog) == 2
        assert done == []

    def test_detects_archived_tasks(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        archive = changes / "archive"
        archive.mkdir()
        (archive / "TASK-001-done.md").write_text("# T1\n")
        in_prog, done = update_progress.collect_tasks(changes)
        assert in_prog == []
        assert len(done) == 1

    def test_separates_in_progress_and_archived(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        archive = changes / "archive"
        archive.mkdir()
        (changes / "TASK-003-wip.md").write_text("# T3\n")
        (archive / "TASK-001-done.md").write_text("# T1\n")
        (archive / "TASK-002-done.md").write_text("# T2\n")
        in_prog, done = update_progress.collect_tasks(changes)
        assert len(in_prog) == 1
        assert len(done) == 2

    def test_ignores_non_md_files(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        (changes / "archive").mkdir()
        (changes / "README.txt").write_text("ignore me\n")
        (changes / "TASK-001-foo.md").write_text("# T1\n")
        in_prog, _ = update_progress.collect_tasks(changes)
        assert len(in_prog) == 1


class TestRenderProgress:
    def test_empty_progress(self):
        result = update_progress.render_progress([], [])
        assert "# Progress" in result
        assert "## Em andamento" in result
        assert "(nenhum)" in result
        assert "## Concluído" in result

    def test_in_progress_tasks_listed(self, tmp_path):
        f = tmp_path / "TASK-001-foo.md"
        f.write_text("# [TASK-001] Foo Task\n")
        result = update_progress.render_progress([f], [])
        assert "TASK-001" in result
        assert "Foo Task" in result

    def test_completed_tasks_listed(self, tmp_path):
        f = tmp_path / "TASK-007-done.md"
        f.write_text("# [TASK-007] Done Task\n")
        result = update_progress.render_progress([], [f])
        assert "TASK-007" in result
        assert "Done Task" in result

    def test_output_ends_with_newline(self):
        result = update_progress.render_progress([], [])
        assert result.endswith("\n")


# ---------------------------------------------------------------------------
# update_readme
# ---------------------------------------------------------------------------


class TestGetModuleDocstring:
    def test_returns_docstring(self, tmp_path):
        f = tmp_path / "mymod.py"
        f.write_text('"""My module description."""\n\nimport os\n')
        assert update_readme.get_module_docstring(f) == "My module description."

    def test_returns_empty_when_no_docstring(self, tmp_path):
        f = tmp_path / "mymod.py"
        f.write_text("import os\n\nx = 1\n")
        assert update_readme.get_module_docstring(f) == ""

    def test_returns_first_line_of_multiline_docstring(self, tmp_path):
        f = tmp_path / "mymod.py"
        f.write_text('"""First line.\n\nSecond paragraph.\n"""\n')
        result = update_readme.get_module_docstring(f)
        assert result == "First line."

    def test_returns_empty_on_syntax_error(self, tmp_path):
        f = tmp_path / "bad.py"
        f.write_text("def broken(\n")
        assert update_readme.get_module_docstring(f) == ""


class TestCollectModules:
    def test_skips_init_files(self, tmp_path):
        (tmp_path / "__init__.py").write_text('"""Package."""\n')
        (tmp_path / "mod.py").write_text('"""A module."""\n')
        modules = update_readme.collect_modules(tmp_path)
        paths = [m[0] for m in modules]
        assert not any("__init__" in p for p in paths)

    def test_collects_nested_modules(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "__init__.py").write_text("")
        (sub / "worker.py").write_text('"""Worker module."""\n')
        modules = update_readme.collect_modules(tmp_path)
        assert len(modules) == 1
        assert "worker.py" in modules[0][0]

    def test_uses_docstring_as_description(self, tmp_path):
        (tmp_path / "mymod.py").write_text('"""My description."""\n')
        modules = update_readme.collect_modules(tmp_path)
        assert modules[0][1] == "My description."

    def test_fallback_description_when_no_docstring(self, tmp_path):
        (tmp_path / "nomod.py").write_text("x = 1\n")
        modules = update_readme.collect_modules(tmp_path)
        assert modules[0][1] != ""


class TestBuildModulesTable:
    def test_produces_markdown_table(self):
        modules = [("app/foo.py", "Foo module"), ("app/bar.py", "Bar module")]
        lines = update_readme.build_modules_table(modules)
        table = "\n".join(lines)
        assert "## Módulos" in table
        assert "| Módulo | Descrição |" in table
        assert "|--------|-----------|" in table
        assert "app/foo.py" in table
        assert "Foo module" in table


class TestReplaceModulesSection:
    def test_replaces_existing_section(self):
        content = "# Title\n\n## Módulos\n\n| old | table |\n\n## Next\n\nmore\n"
        modules = [("app/x.py", "Desc X")]
        result = update_readme.replace_modules_section(content, modules)
        assert "old | table" not in result
        assert "app/x.py" in result
        assert "## Next" in result

    def test_preserves_content_before_and_after(self):
        content = "# Title\n\n## Intro\n\nIntro text\n\n## Módulos\n\n| old |\n\n## After\n\nfoo\n"
        modules = [("app/y.py", "Desc Y")]
        result = update_readme.replace_modules_section(content, modules)
        assert "Intro text" in result
        assert "## After" in result
        assert "foo" in result

    def test_appends_when_section_missing(self):
        content = "# Title\n\nSome text\n"
        modules = [("app/z.py", "Desc Z")]
        result = update_readme.replace_modules_section(content, modules)
        assert "## Módulos" in result
        assert "app/z.py" in result

    def test_output_ends_with_newline(self):
        content = "## Módulos\n\n| x |\n"
        result = update_readme.replace_modules_section(content, [])
        assert result.endswith("\n")
