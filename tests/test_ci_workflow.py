"""Tests for .github/workflows/ci.yml — TASK-008."""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_file_exists():
    assert CI_WORKFLOW.exists(), f"{CI_WORKFLOW} não encontrado"


def test_ci_workflow_has_pytest():
    content = CI_WORKFLOW.read_text()
    assert "pytest" in content, "ci.yml deve conter step de pytest"


def test_ci_workflow_has_ruff():
    content = CI_WORKFLOW.read_text()
    assert "ruff" in content, "ci.yml deve conter step de ruff"


def test_ci_workflow_has_merge_group_trigger():
    content = CI_WORKFLOW.read_text()
    assert "merge_group" in content, "ci.yml deve ter trigger merge_group"
