import os
from pathlib import Path

from app.pipeline import ScanResult


def _scans_dir() -> Path:
    return Path(os.getenv("DATA_DIR", "data")) / "scans"


def save_scan(result: ScanResult) -> Path:
    scans_dir = _scans_dir()
    scans_dir.mkdir(parents=True, exist_ok=True)
    path = scans_dir / f"{result.date}.json"
    path.write_text(result.model_dump_json(indent=2))
    return path


def load_scan(date_str: str) -> ScanResult | None:
    path = _scans_dir() / f"{date_str}.json"
    if not path.exists():
        return None
    return ScanResult.model_validate_json(path.read_text())


def get_latest_scan() -> ScanResult | None:
    scans_dir = _scans_dir()
    if not scans_dir.exists():
        return None
    files = sorted(scans_dir.glob("*.json"), reverse=True)
    if not files:
        return None
    return ScanResult.model_validate_json(files[0].read_text())
