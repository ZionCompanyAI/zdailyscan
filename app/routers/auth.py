from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeSerializer

from app.config import Settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _serializer(secret: str) -> URLSafeSerializer:
    return URLSafeSerializer(secret, salt="session")


def get_current_user(request: Request) -> str | None:
    """Return username from signed session cookie, or None if absent/invalid."""
    cookie = request.cookies.get("session")
    if not cookie:
        return None
    s = Settings()
    try:
        data = _serializer(s.dashboard_session_secret).loads(cookie)
        return data.get("user")
    except BadSignature:
        return None


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
@router.post("/auth/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    s = Settings()
    if username == s.dashboard_username and password == s.dashboard_password:
        cookie = _serializer(s.dashboard_session_secret).dumps({"user": username})
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie("session", cookie, httponly=True)
        return response
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": "Usuário ou senha inválidos"},
        status_code=401,
    )


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response
