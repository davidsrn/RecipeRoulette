"""
app.py — FastAPI web server for RecipeRoulette.

Run:
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload
"""

import hmac
import json
import os
import re
import sys
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import Cookie, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import func

from models import CATEGORIES, MOODS, Recipe, get_session, init_db

import google.generativeai as genai

load_dotenv()

APP_PASSWORD = os.getenv("APP_PASSWORD", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
COOKIE_NAME = "rr_session"
COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 days
# True when running behind Railway's HTTPS termination (or any production env)
SECURE_COOKIES = os.getenv("RAILWAY_ENVIRONMENT") is not None

# ── Startup validation ────────────────────────────────────────────────────────

_missing = [
    name for name, val in [
        ("APP_PASSWORD", APP_PASSWORD),
        ("SECRET_KEY", SECRET_KEY),
    ]
    if not val or val == "change-me"
]
if _missing:
    print(f"ERROR: Required env vars not set or left at defaults: {', '.join(_missing)}")
    print("Set them in your .env file (local) or Railway Variables (production).")
    sys.exit(1)

serializer = URLSafeTimedSerializer(SECRET_KEY)

# ── App lifecycle ─────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
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
    if hmac.compare_digest(password, APP_PASSWORD):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key=COOKIE_NAME,
            value=make_session_cookie(),
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=SECURE_COOKIES,
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

        query = query.filter(Recipe.done == False)
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
    new_title = body.get("title")  # optional free-text, no allowlist needed
    new_done = body.get("done")  # bool or None

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
        if new_title is not None:
            recipe.title = new_title.strip() or None  # empty string → null
        if new_done is not None:
            recipe.done = bool(new_done)

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








@app.post("/api/recipe/{recipe_id}/analyze")
async def analyze_recipe(recipe_id: int, rr_session: Optional[str] = Cookie(default=None)):
    """Use Gemini to parse the stored og:description into ingredients, instructions, and mood."""
    if not rr_session or not verify_session_cookie(rr_session):
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not configured")

    with get_session() as session:
        recipe = session.get(Recipe, recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        if not recipe.description:
            raise HTTPException(status_code=422, detail="No description available to analyze")
        description = recipe.description

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""Extract recipe information from this Instagram post caption.
Return ONLY a valid JSON object with exactly these fields:
- "ingredients": a newline-separated list of ingredients (null if none found)
- "instructions": numbered steps as a newline-separated string (null if none found)
- "mood": one of exactly: "None", "Quick", "Date Night", "Healthy", "Comfort Food", "Fancy", "Lazy Day", "Meal Prep"

Caption:
{description}

Return only the JSON object, no markdown, no extra text."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown code fences if the model adds them
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text).strip()
        parsed = json.loads(text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {exc}")

    ingredients = parsed.get("ingredients") or None
    instructions = parsed.get("instructions") or None
    mood = parsed.get("mood") or "None"
    if mood not in MOODS:
        mood = "None"

    with get_session() as session:
        recipe = session.get(Recipe, recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        if ingredients:
            recipe.ingredients = ingredients
        if instructions:
            recipe.instructions = instructions
        recipe.mood = mood
        session.commit()
        return JSONResponse(recipe.to_dict())


@app.get("/api/thumbnail/{recipe_id}")
async def thumbnail_proxy(recipe_id: int, rr_session: Optional[str] = Cookie(default=None)):
    """Serve stored thumbnail image bytes from DB — no external request."""
    if not rr_session or not verify_session_cookie(rr_session):
        raise HTTPException(status_code=401, detail="Not authenticated")

    with get_session() as session:
        recipe = session.get(Recipe, recipe_id)
        if not recipe or not recipe.thumbnail_data:
            raise HTTPException(status_code=404, detail="No thumbnail")
        return Response(
            content=recipe.thumbnail_data,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=604800"},  # 7 days
        )


