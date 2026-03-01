"""
app.py — FastAPI web server for RecipeRoulette.

Run:
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import Cookie, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import func

from models import CATEGORIES, MOODS, Recipe, get_session, init_db

load_dotenv()

APP_PASSWORD = os.getenv("APP_PASSWORD", "")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
COOKIE_NAME = "rr_session"
COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 days

serializer = URLSafeTimedSerializer(SECRET_KEY)

# ── App lifecycle ─────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Auth helpers ──────────────────────────────────────────────────────────────


def make_session_cookie() -> str:
    return serializer.dumps({"authed": True})


def verify_session_cookie(token: str) -> bool:
    try:
        data = serializer.loads(token, max_age=COOKIE_MAX_AGE)
        return data.get("authed") is True
    except (SignatureExpired, BadSignature):
        return False


def require_auth(rr_session: Optional[str] = Cookie(default=None)) -> bool:
    """Dependency — raises redirect to /login if not authenticated."""
    if not rr_session or not verify_session_cookie(rr_session):
        raise HTTPException(status_code=307, headers={"Location": "/login"})
    return True


# ── Auth routes ───────────────────────────────────────────────────────────────


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if password == APP_PASSWORD:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key=COOKIE_NAME,
            value=make_session_cookie(),
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
        )
        return response
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": "Wrong password."}, status_code=401
    )


@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response


# ── Main pages ────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, rr_session: Optional[str] = Cookie(default=None)):
    if not rr_session or not verify_session_cookie(rr_session):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "categories": CATEGORIES, "moods": MOODS},
    )


@app.get("/manage", response_class=HTMLResponse)
async def manage(request: Request, rr_session: Optional[str] = Cookie(default=None)):
    if not rr_session or not verify_session_cookie(rr_session):
        return RedirectResponse(url="/login", status_code=303)

    with get_session() as session:
        recipes = session.query(Recipe).order_by(Recipe.date_added.desc()).all()
        recipes_data = [r.to_dict() for r in recipes]

    return templates.TemplateResponse(
        "manage.html",
        {
            "request": request,
            "recipes": recipes_data,
            "categories": CATEGORIES,
            "moods": MOODS,
        },
    )


# ── API ───────────────────────────────────────────────────────────────────────


@app.get("/api/spin")
async def spin(
    rr_session: Optional[str] = Cookie(default=None),
    category: Optional[str] = None,
    mood: Optional[str] = None,
):
    if not rr_session or not verify_session_cookie(rr_session):
        raise HTTPException(status_code=401, detail="Not authenticated")

    with get_session() as session:
        query = session.query(Recipe)

        if category and category != "All":
            query = query.filter(Recipe.category == category)
        if mood and mood != "All":
            query = query.filter(Recipe.mood == mood)

        recipe = query.order_by(func.random()).first()

    if not recipe:
        raise HTTPException(status_code=404, detail="No recipes match those filters.")

    return JSONResponse(recipe.to_dict())


@app.patch("/api/recipe/{recipe_id}")
async def update_recipe(
    recipe_id: int,
    request: Request,
    rr_session: Optional[str] = Cookie(default=None),
):
    if not rr_session or not verify_session_cookie(rr_session):
        raise HTTPException(status_code=401, detail="Not authenticated")

    body = await request.json()
    new_category = body.get("category")
    new_mood = body.get("mood")

    if new_category and new_category not in CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Invalid category: {new_category}")
    if new_mood and new_mood not in MOODS:
        raise HTTPException(status_code=422, detail=f"Invalid mood: {new_mood}")

    with get_session() as session:
        recipe = session.get(Recipe, recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        if new_category:
            recipe.category = new_category
        if new_mood:
            recipe.mood = new_mood

        session.commit()
        return JSONResponse(recipe.to_dict())


@app.get("/api/categories")
async def get_categories(rr_session: Optional[str] = Cookie(default=None)):
    if not rr_session or not verify_session_cookie(rr_session):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return JSONResponse(CATEGORIES)


@app.get("/api/moods")
async def get_moods(rr_session: Optional[str] = Cookie(default=None)):
    if not rr_session or not verify_session_cookie(rr_session):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return JSONResponse(MOODS)
