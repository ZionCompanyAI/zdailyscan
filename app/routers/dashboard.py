import asyncio
import logging
import os
import uuid as uuid_lib

import httpx
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import app.storage as _storage
from app.config import Settings
from app.pipeline import CATEGORIES, ScanResult, get_active_categories, run_daily_scan
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

_scan_status: dict[str, dict] = {}

CATEGORY_NAMES: dict[str, str] = {
    "200003655": "Consumer Electronics",
    "100003070": "Phones & Telecom",
    "200000783": "Computer & Office",
    "200000828": "Home & Garden",
    "200000834": "Sports & Entertainment",
}


def _require_user(request: Request):
    user = get_current_user(request)
    if not user:
        return None, RedirectResponse(url="/login", status_code=303)
    return user, None


def _load_all_products() -> list[dict]:
    """Aggregate products from all scans, deduplicating by product_id (keep latest)."""
    seen: dict[str, dict] = {}
    if not _storage.SCANS_DIR.exists():
        return []
    for scan_file in sorted(_storage.SCANS_DIR.glob("*.json"), reverse=True):
        try:
            scan = ScanResult.model_validate_json(scan_file.read_text())
            for p in scan.products:
                if p.product_id not in seen:
                    seen[p.product_id] = p.model_dump()
        except Exception:
            continue
    return list(seen.values())


async def _run_scan_background(scan_id: str, categories: list[str] | None = None) -> None:
    _scan_status[scan_id] = {"status": "running", "product_count": 0}
    try:
        result = await run_daily_scan(scan_id, categories=categories)
        _storage.save_scan(result)
        _scan_status[scan_id] = {"status": "completed", "product_count": len(result.products)}
    except Exception:
        logger.exception("scan failed: %s", scan_id)
        _scan_status[scan_id] = {"status": "failed", "product_count": 0}


# ---------------------------------------------------------------------------
# Dashboard index
# ---------------------------------------------------------------------------


@router.get("", response_class=HTMLResponse)
def dashboard_index(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    dates: list[str] = []
    if _storage.SCANS_DIR.exists():
        dates = sorted(
            [p.stem for p in _storage.SCANS_DIR.glob("*.json")],
            reverse=True,
        )

    return templates.TemplateResponse(request, "dashboard.html", {"dates": dates, "user": user})


# ---------------------------------------------------------------------------
# New HTML pages — must be registered BEFORE /{date} catch-all
# ---------------------------------------------------------------------------


@router.get("/explorer", response_class=HTMLResponse)
def dashboard_explorer(
    request: Request,
    category_id: str | None = None,
    min_score: float = 0,
    sort_by: str = "score",
    limit: int = 50,
):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    products = _load_all_products()

    if min_score > 0:
        products = [p for p in products if p["score_total"] * 100 >= min_score]

    if sort_by == "price":
        products.sort(key=lambda p: p["import_cost_brl"])
    elif sort_by == "demand":
        products.sort(key=lambda p: p["demand_count"], reverse=True)
    else:
        products.sort(key=lambda p: p["score_total"], reverse=True)

    settings = Settings()

    return templates.TemplateResponse(
        request,
        "explorer.html",
        {
            "products": products[:limit],
            "user": user,
            "category_id": category_id or "",
            "min_score": min_score,
            "sort_by": sort_by,
            "limit": limit,
            "category_names": CATEGORY_NAMES,
            "tracking_id": settings.aliexpress_tracking_id,
        },
    )


@router.get("/scanner", response_class=HTMLResponse)
def dashboard_scanner(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    scans = []
    if _storage.SCANS_DIR.exists():
        for scan_file in sorted(_storage.SCANS_DIR.glob("*.json"), reverse=True):
            try:
                scan = ScanResult.model_validate_json(scan_file.read_text())
                scans.append(
                    {
                        "scan_id": scan.scan_id,
                        "date": scan.date,
                        "product_count": len(scan.products),
                        "total_scanned": scan.total_scanned,
                        "total_viable": scan.total_viable,
                        "status": "completed",
                    }
                )
            except Exception:
                continue

    active_ids = set(get_active_categories())
    return templates.TemplateResponse(
        request,
        "scanner.html",
        {
            "scans": scans,
            "user": user,
            "scraper_mode": os.environ.get("SCRAPER_MODE", "crawl4ai"),
            "categories": [
                {"id": k, "name": v, "active": k in active_ids}
                for k, v in CATEGORY_NAMES.items()
            ],
        },
    )


@router.get("/settings", response_class=HTMLResponse)
def dashboard_settings(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    settings = Settings()

    def _mask(value: str, visible: int = 4) -> str:
        if not value or len(value) <= visible:
            return "***"
        return value[:visible] + "***"

    active_ids = set(get_active_categories())
    all_categories = [
        {"id": k, "name": v, "active": k in active_ids} for k, v in CATEGORY_NAMES.items()
    ]
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "user": user,
            "telegram_bot_token_masked": _mask(settings.telegram_bot_token),
            "telegram_chat_id": settings.telegram_chat_id,
            "scraper_mode": os.environ.get("SCRAPER_MODE", "crawl4ai"),
            "usd_brl_rate": settings.usd_brl_rate,
            "categories": all_categories,
            "aliexpress_session_cookies": settings.aliexpress_session_cookies,
        },
    )


@router.post("/settings")
async def dashboard_settings_post(
    request: Request,
    aliexpress_session_cookies: str = Form(default=""),
):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    if aliexpress_session_cookies:
        os.environ["ALIEXPRESS_SESSION_COOKIES"] = aliexpress_session_cookies
    return RedirectResponse(url="/dashboard/settings", status_code=303)


@router.post("/settings/categories")
async def dashboard_settings_categories(
    request: Request,
    categories: list[str] = Form(default=[]),
):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    valid = set(CATEGORIES)
    selected = [c for c in categories if c in valid]
    os.environ["SCAN_CATEGORIES"] = ",".join(selected)
    return RedirectResponse(url="/dashboard/settings", status_code=303)


# ---------------------------------------------------------------------------
# JSON API endpoints
# ---------------------------------------------------------------------------


@router.get("/products")
def dashboard_products(
    request: Request,
    category_id: str | None = None,
    min_score: float = 0,
    sort_by: str = "score",
    limit: int = 50,
):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    products = _load_all_products()

    if min_score > 0:
        products = [p for p in products if p["score_total"] * 100 >= min_score]

    if sort_by == "price":
        products.sort(key=lambda p: p["import_cost_brl"])
    elif sort_by == "demand":
        products.sort(key=lambda p: p["demand_count"], reverse=True)
    else:
        products.sort(key=lambda p: p["score_total"], reverse=True)

    return {"products": products[:limit]}


@router.get("/scans")
def dashboard_scans(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    scans = []
    if _storage.SCANS_DIR.exists():
        for scan_file in sorted(_storage.SCANS_DIR.glob("*.json"), reverse=True):
            try:
                scan = ScanResult.model_validate_json(scan_file.read_text())
                scans.append(
                    {
                        "scan_id": scan.scan_id,
                        "date": scan.date,
                        "product_count": len(scan.products),
                        "status": "completed",
                    }
                )
            except Exception:
                continue

    return {"scans": scans}


@router.post("/scan/trigger")
async def dashboard_scan_trigger(
    request: Request,
    categories: list[str] = Form(default=[]),
):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    scan_id = str(uuid_lib.uuid4())
    cats = categories if categories else None
    asyncio.create_task(_run_scan_background(scan_id, categories=cats))

    return JSONResponse({"scan_id": scan_id, "status": "running"})


@router.get("/scan/{scan_id}/status")
def dashboard_scan_status(request: Request, scan_id: str):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    status = _scan_status.get(scan_id)
    if status is None:
        raise HTTPException(status_code=404, detail="scan_id not found")

    return {"scan_id": scan_id, **status}


@router.post("/settings/telegram-test")
async def dashboard_telegram_test(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    settings = Settings()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.mc_url}/telegram/reply",
                headers={"x-api-key": settings.mc_api_key},
                json={
                    "chat_id": settings.telegram_chat_id,
                    "text": "🔔 ZDailyScan — teste de configuração OK",
                    "parse_mode": "Markdown",
                },
            )
            resp.raise_for_status()
            return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "detail": str(e)})


# ---------------------------------------------------------------------------
# Legacy trigger (keep for backwards compat)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Report by date — catch-all (must be LAST)
# ---------------------------------------------------------------------------


@router.get("/{date}", response_class=HTMLResponse)
def dashboard_report(request: Request, date: str):
    user, redirect = _require_user(request)
    if redirect:
        return redirect

    scan = _storage.load_scan(date)
    if scan is None:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    return templates.TemplateResponse(request, "report.html", {"scan": scan, "user": user})
