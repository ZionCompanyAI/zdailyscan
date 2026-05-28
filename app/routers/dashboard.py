import os

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.routers.auth import get_current_user
from app.storage import SCANS_DIR, load_scan

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")


def _require_user(request: Request):
    """Return username or RedirectResponse to /login."""
    user = get_current_user(request)
    if not user:
        return None, RedirectResponse(url="/login", status_code=303)
    return user, None


@router.get("", response_class=HTMLResponse)
def dashboard_index(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    dates: list[str] = []
    if SCANS_DIR.exists():
        dates = sorted(
            [p.stem for p in SCANS_DIR.glob("*.json")],
            reverse=True,
        )

    return templates.TemplateResponse(
        request, "dashboard.html", {"dates": dates, "user": user}
    )


@router.get("/{date}", response_class=HTMLResponse)
def dashboard_report(request: Request, date: str):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    scan = load_scan(date)
    if scan is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    return templates.TemplateResponse(
        request, "report.html", {"scan": scan, "user": user}
    )


@router.post("/scan")
def dashboard_scan(request: Request):
    _user, redirect = _require_user(request)
    if redirect:
        return redirect

    api_key = os.environ.get("SCAN_API_KEY", "test")
    try:
        httpx.post(
            "http://localhost:8000/scan/run",
            headers={"x-api-key": api_key},
            timeout=5,
        )
    except Exception:
        pass

    return RedirectResponse(url="/dashboard", status_code=303)
