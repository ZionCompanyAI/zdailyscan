import os
import uuid
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.pipeline import ScanResult, run_daily_scan
from app.routers import auth, dashboard
from app.scheduler import create_scheduler
from app.scrapers import get_hot_products
from app.storage import get_latest_scan, load_scan, save_scan


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="ZDailyScan", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)


@app.get("/")
def root(request: Request):
    from app.routers.auth import get_current_user

    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok", "service": "zdailyscan"}


@app.get("/scan/latest", response_model=ScanResult)
def scan_latest():
    result = get_latest_scan()
    if result is None:
        raise HTTPException(status_code=404, detail="No scans found")
    return result


@app.get("/scan/{date}", response_model=ScanResult)
def scan_by_date(date: str):
    result = load_scan(date)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return result


@app.post("/scan/run")
async def scan_run(
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(...),
) -> dict:
    expected_key = os.environ.get("SCAN_API_KEY", "test")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    scan_id = str(uuid.uuid4())

    async def _do_scan() -> None:
        result = await run_daily_scan(scan_id=scan_id)
        save_scan(result)

    background_tasks.add_task(_do_scan)
    return {"status": "started", "scan_id": scan_id}


@app.get("/scrapers/aliexpress")
async def scrape_aliexpress(category: str = "200003655", limit: int = 20):
    # min_rating=0.0: do not filter out products returned by Firecrawl fallback
    # which may not include a rating field (defaults to 0.0 in AliProduct).
    products = await get_hot_products(category_id=category, min_rating=0.0, max_results=limit)
    return {"products": [p.model_dump() for p in products], "count": len(products)}
