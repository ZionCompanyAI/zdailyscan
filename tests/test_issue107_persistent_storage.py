"""
Issue #107 — scan results stored in ephemeral filesystem.
DATA_DIR env var must control the storage path so Railway volumes work.
"""

import app.storage as storage_module

from app.pipeline import ScanResult


def _make_scan_result() -> ScanResult:
    return ScanResult(
        scan_id="test-scan-107",
        date="2026-06-01",
        products=[],
        total_scanned=0,
        total_viable=0,
    )


def test_scan_persists_after_restart(tmp_path, monkeypatch):
    """save_scan writes to DATA_DIR path — simulates Railway volume surviving restart."""
    data_dir = tmp_path / "vol"
    monkeypatch.setenv("DATA_DIR", str(data_dir))

    result = _make_scan_result()
    path = storage_module.save_scan(result)

    # File must land inside DATA_DIR, not in hardcoded 'data/scans'
    assert path.is_relative_to(data_dir), (
        f"Expected path inside DATA_DIR={data_dir}, got {path}"
    )
    # Read-back must also use DATA_DIR (simulates new instance pointing at same volume)
    loaded = storage_module.load_scan(result.date)
    assert loaded is not None
    assert loaded.scan_id == result.scan_id


def test_scan_latest_persists(tmp_path, monkeypatch):
    """/scan/latest reads from DATA_DIR — survives redeploy when volume is mounted."""
    data_dir = tmp_path / "vol"
    monkeypatch.setenv("DATA_DIR", str(data_dir))

    result = _make_scan_result()
    path = storage_module.save_scan(result)

    assert path.is_relative_to(data_dir), (
        f"Expected path inside DATA_DIR={data_dir}, got {path}"
    )
    latest = storage_module.get_latest_scan()
    assert latest is not None
    assert latest.scan_id == result.scan_id


def test_default_data_dir_unchanged(tmp_path, monkeypatch):
    """When DATA_DIR is not set, storage falls back to 'data/scans' (no regression)."""
    monkeypatch.delenv("DATA_DIR", raising=False)

    scans_dir = storage_module._scans_dir()
    assert str(scans_dir) == "data/scans"
