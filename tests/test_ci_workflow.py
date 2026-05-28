"""Tests for .github/workflows/ci.yml existence and required content."""
import os

WORKFLOW_PATH = os.path.join(
    os.path.dirname(__file__), "..", ".github", "workflows", "ci.yml"
)


def _read_workflow() -> str:
    with open(WORKFLOW_PATH) as f:
        return f.read()


def test_ci_workflow_file_exists():
    assert os.path.isfile(WORKFLOW_PATH), ".github/workflows/ci.yml deve existir"


def test_ci_workflow_has_pytest():
    content = _read_workflow()
    assert "pytest" in content, "ci.yml deve conter step de pytest"


def test_ci_workflow_has_ruff():
    content = _read_workflow()
    assert "ruff" in content, "ci.yml deve conter step de ruff"


def test_ci_workflow_has_merge_group_trigger():
    content = _read_workflow()
    assert "merge_group" in content, "ci.yml deve ter trigger merge_group para Merge Queue"


def test_ci_workflow_has_pull_request_trigger():
    content = _read_workflow()
    assert "pull_request" in content, "ci.yml deve ter trigger pull_request"


def test_ci_workflow_has_python_setup():
    content = _read_workflow()
    assert "actions/setup-python" in content, "ci.yml deve configurar Python"


def test_ci_workflow_uses_python_311():
    content = _read_workflow()
    assert "3.11" in content, "ci.yml deve usar Python 3.11 (conforme pyproject.toml)"
