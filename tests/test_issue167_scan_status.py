"""RED tests — issue #167: ScanResult.status None + /scan/run não atualiza _scan_status."""
import json
import os
from unittest.mock import patch

os.environ.setdefault("ALIEXPRESS_APP_KEY", "test")
os.environ.setdefault("ALIEXPRESS_APP_SECRET", "test")
os.environ.setdefault("ALIEXPRESS_TRACKING_ID", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("MC_API_KEY", "test")
os.environ.setdefault("MC_URL", "http://localhost")
os.environ.setdefault("DASHBOARD_USERNAME", "admin")
os.environ.setdefault("DASHBOARD_PASSWORD", "secret")
os.environ.setdefault("DASHBOARD_SESSION_SECRET", "test-secret-key")


# ---------------------------------------------------------------------------
# Fix 1 — ScanResult.status defaults to "completed"
# ---------------------------------------------------------------------------


def test_scan_result_has_status_field_defaulting_to_completed():
    from app.pipeline import ScanResult

    result = ScanResult(
        scan_id="abc-123",
        date="2026-06-02",
        products=[],
        total_scanned=10,
        total_viable=2,
    )
    assert result.status == "completed"


def test_scan_result_status_is_serialized_to_json():
    from app.pipeline import ScanResult

    result = ScanResult(
        scan_id="abc-123",
        date="2026-06-02",
        products=[],
        total_scanned=10,
        total_viable=2,
    )
    data = json.loads(result.model_dump_json())
    assert "status" in data
    assert data["status"] == "completed"


def test_scan_result_status_can_be_set_explicitly():
    from app.pipeline import ScanResult

    result = ScanResult(
        scan_id="abc-123",
        date="2026-06-02",
        status="running",
        products=[],
        total_scanned=0,
        total_viable=0,
    )
    assert result.status == "running"


def test_scan_result_loaded_from_json_without_status_defaults_to_completed():
    """Scans gravados antes do fix (sem campo status) devem deserializar como completed."""
    from app.pipeline import ScanResult

    old_json = json.dumps({
        "scan_id": "legacy-id",
        "date": "2026-01-01",
        "products": [],
        "total_scanned": 5,
        "total_viable": 1,
    })
    result = ScanResult.model_validate_json(old_json)
    assert result.status == "completed"


# ---------------------------------------------------------------------------
# Fix 2 — GET /scan/latest inclui status no response
# ---------------------------------------------------------------------------


def test_scan_latest_returns_status_field(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app.pipeline import ScanResult
    import app.storage as storage

    scan = ScanResult(
        scan_id="test-scan",
        date="2026-06-02",
        products=[],
        total_scanned=5,
        total_viable=1,
    )
    storage.save_scan(scan)

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, follow_redirects=False)
    resp = client.get("/scan/latest", headers={"x-api-key": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] == "completed"


# ---------------------------------------------------------------------------
# Fix 3 — POST /scan/run atualiza _scan_status no dashboard
# ---------------------------------------------------------------------------


async def test_scan_run_updates_scan_status_dict(monkeypatch):
    """POST /scan/run deve registrar scan_id em _scan_status do dashboard."""
    monkeypatch.setenv("SCAN_API_KEY", "secret-key")

    from app.pipeline import ScanResult

    _fake_result = ScanResult(
        scan_id="will-be-overridden",
        date="2026-06-02",
        products=[],
        total_scanned=3,
        total_viable=1,
    )

    async def _fake_run(scan_id, categories=None):
        _fake_result.scan_id = scan_id
        return _fake_result

    with patch("app.pipeline.run_daily_scan", side_effect=_fake_run):
        with patch("app.storage.save_scan"):
            from fastapi.testclient import TestClient
            from app.main import app
            from app.routers import dashboard as dash_mod

            # Limpar estado global antes do teste
            dash_mod._scan_status.clear()

            client = TestClient(app, follow_redirects=False)
            resp = client.post("/scan/run", headers={"x-api-key": "secret-key"})

    assert resp.status_code == 200
    body = resp.json()
    scan_id = body["scan_id"]

    # O background task foi executado sincronamente pelo TestClient
    assert scan_id in dash_mod._scan_status, (
        f"_scan_status deve conter {scan_id!r}; contém: {list(dash_mod._scan_status)}"
    )
    assert dash_mod._scan_status[scan_id]["status"] == "completed"


async def test_scan_run_status_endpoint_returns_completed_after_run(monkeypatch):
    """GET /dashboard/scan/{id}/status deve retornar completed após POST /scan/run."""
    monkeypatch.setenv("SCAN_API_KEY", "secret-key")
    monkeypatch.setenv("DASHBOARD_USERNAME", "admin")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    monkeypatch.setenv("DASHBOARD_SESSION_SECRET", "test-secret-key")

    from app.pipeline import ScanResult

    async def _fake_run(scan_id, categories=None):
        return ScanResult(
            scan_id=scan_id,
            date="2026-06-02",
            products=[],
            total_scanned=2,
            total_viable=0,
        )

    with patch("app.pipeline.run_daily_scan", side_effect=_fake_run):
        with patch("app.storage.save_scan"):
            from fastapi.testclient import TestClient
            from app.main import app
            from app.routers import dashboard as dash_mod
            from itsdangerous import URLSafeSerializer

            dash_mod._scan_status.clear()

            client = TestClient(app, follow_redirects=False)
            resp = client.post("/scan/run", headers={"x-api-key": "secret-key"})
            assert resp.status_code == 200
            scan_id = resp.json()["scan_id"]

            # Build session cookie to access /dashboard/scan/{id}/status
            s = URLSafeSerializer("test-secret-key", salt="session")
            cookie = s.dumps({"user": "admin"})
            status_resp = client.get(
                f"/dashboard/scan/{scan_id}/status",
                cookies={"session": cookie},
            )

    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "completed"
