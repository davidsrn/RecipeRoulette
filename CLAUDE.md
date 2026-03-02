# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation

Read these files before making changes:
- `ARCHITECTURE.md` — system design, DB schema, API routes, design tokens
- `DEVELOPMENT.md` — coding conventions, common pitfalls, testing checklist
- `PLAN.md` — implementation tracker (all 6 phases complete ✅)

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in secrets
cp .env.example .env

# One-time: import seed data (96 Instagram URLs)
python import_csv.py

# Web server (Terminal 1) — reloads on file changes
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Telegram bot (Terminal 2)
python bot.py
```

Access the web app at `http://localhost:8000`.

## Architecture

Two processes share a single SQLite file (`recipes.db`):

1. **`app.py`** — FastAPI web server with Jinja2 templating. Serves the roulette UI (`/`), management page (`/manage`), and REST API (`/api/spin`, `/api/recipe/{id}`, etc.). Auth via HMAC-signed cookies (`itsdangerous`).

2. **`bot.py`** — Telegram bot (python-telegram-bot v20, async long-polling). Listens for Instagram URLs from a single authorized user ID, deduplicates, and inserts into DB with best-effort metadata fetch.

**`models.py`** is imported by both — defines the `Recipe` ORM model, `get_session()` context manager, and `init_db()`. SQLite WAL mode enables concurrent access.

**Frontend** is vanilla JS (`static/app.js`) + Tailwind CDN + Jinja2 templates. No build step.

**AI integration:** `POST /api/recipe/{id}/analyze` calls Gemini 2.0 Flash to extract ingredients, instructions, and mood from the stored `og:description`.

## Key Conventions

**Python:**
- SQLAlchemy 2.x style only — always use `with get_session() as session:`, never raw SQL
- Validate `category` and `mood` values against `CATEGORIES`/`MOODS` allowlists in `models.py` before any DB write
- `async/await` throughout — FastAPI and PTB v20 are both fully async
- Use PTB v20 `ApplicationBuilder` pattern, not the legacy `Updater`

**JavaScript:**
- All JS lives in `static/app.js` — no inline `<script>` blocks in HTML
- Use `fetch()` with `async/await`; always catch errors and show a toast, never silently fail

**HTML/CSS:**
- All pages extend `templates/base.html` (Tailwind CDN, Google Fonts Inter, warm color palette)
- Mobile-first: design for 375px width
- Primary color: `#F97316` (orange-500); accent: `#FBBF24` (amber-400)

## Environment Variables

Required in `.env`:
```
TG_TOKEN=           # Telegram bot token from @BotFather
AUTHORIZED_USER_ID= # Telegram numeric user ID from @userinfobot
APP_PASSWORD=       # Web app password
SECRET_KEY=         # 32-char random string for cookie signing
DB_PATH=            # Default: ./recipes.db
GEMINI_API_KEY=     # For /api/recipe/{id}/analyze
```

`RAILWAY_ENVIRONMENT` is auto-set by Railway and enables `Secure` flag on cookies.

## Deployment

Deployed on Railway as a single service (Docker). `start.sh` runs `bot.py` in background then `app.py` in foreground. Requires a persistent volume mounted at `/data` with `DB_PATH=/data/recipes.db`. On first boot, `import_csv.py` runs automatically if the DB doesn't exist.
