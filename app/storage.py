from pathlib import Path

from app.pipeline import ScanResult

SCANS_DIR = Path("data/scans")


def save_scan(result: ScanResult) -> Path:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    path = SCANS_DIR / f"{result.date}.json"
    path.write_text(result.model_dump_json(indent=2))
    return path


def load_scan(date_str: str) -> ScanResult | None:
    path = SCANS_DIR / f"{date_str}.json"
    if not path.exists():
        return None
    return ScanResult.model_validate_json(path.read_text())


def get_latest_scan() -> ScanResult | None:
    if not SCANS_DIR.exists():
        return None
    files = sorted(SCANS_DIR.glob("*.json"), reverse=True)
    if not files:
        return None
    return ScanResult.model_validate_json(files[0].read_text())
