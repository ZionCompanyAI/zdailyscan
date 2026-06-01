"""
Issue #114 — polling de status do scan perdido ao navegar entre páginas.
O scan_id deve ser salvo em sessionStorage para retomar o polling ao voltar.
"""

import re
from pathlib import Path


TEMPLATE = Path("app/templates/scanner.html").read_text()


def test_session_storage_set_on_scan_start():
    """sessionStorage.setItem('active_scan_id', ...) deve existir no template."""
    assert "sessionStorage.setItem('active_scan_id'" in TEMPLATE


def test_session_storage_get_on_page_load():
    """sessionStorage.getItem('active_scan_id') deve ser lido no carregamento da página."""
    assert "sessionStorage.getItem('active_scan_id')" in TEMPLATE


def test_session_storage_removed_on_completion():
    """sessionStorage.removeItem('active_scan_id') deve ser chamado ao completar o scan."""
    assert "sessionStorage.removeItem('active_scan_id')" in TEMPLATE


def test_start_polling_function_exists():
    """startPolling deve ser uma função reutilizável (não inline no submit)."""
    assert "function startPolling(" in TEMPLATE


def test_polling_resumes_on_page_load():
    """startPolling deve ser chamado com o id recuperado do sessionStorage."""
    assert re.search(r"if\s*\(id\)\s*startPolling\(id\)", TEMPLATE)


def test_stop_condition_uses_not_running():
    """Polling deve parar quando status != 'running' (não apenas completed/failed hardcoded)."""
    assert "s.status !== 'running'" in TEMPLATE
