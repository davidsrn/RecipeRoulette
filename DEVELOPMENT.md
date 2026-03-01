# RecipeRoulette — Developer & Agent Instructions

> For: Future AI agents, the developer (David), or any contributor.
> Read ARCHITECTURE.md first for system design context.
> Check PLAN.md to see what is done and what needs to be built next.

---

## Quick Start for Agents

**Before writing any code:**
1. Read `PLAN.md` — find the first `⬜ Pending` task in the next incomplete Phase.
2. Read `ARCHITECTURE.md` — understand how that component fits the system.
3. Read existing files in the project before creating or modifying them.
4. When done with a task, update `PLAN.md` (change `⬜` to `✅`).

---

## Coding Conventions

### Python
- **Python 3.11+** assumed.
- All async code uses `async/await` (FastAPI + python-telegram-bot v20 are both async).
- Use `python-dotenv` to load `.env` at the top of every entry-point file (`app.py`, `bot.py`, `import_csv.py`).
- SQLAlchemy 2.x style (not legacy 1.x). Use `Session` context managers:
  ```python
  with get_session() as session:
      ...
  ```
- Always validate category/mood values against the predefined allowlist before writing to DB (see ARCHITECTURE.md §3).
- Never use raw SQL strings — use SQLAlchemy ORM queries only.

### JavaScript
- Vanilla JS only — no frameworks, no build step.
- All JS lives in `static/app.js`. No inline `<script>` blocks in HTML (except tiny initializers).
- Use `fetch()` with `async/await` for all API calls.
- Error handling: catch errors and show a toast/snackbar message to the user, never silently fail.

### HTML / CSS
- Tailwind CSS via CDN (no build step needed for v1).
- `base.html` is the Jinja2 parent template — all pages extend it.
- Mobile-first: design for 375px width, test at 390px (iPhone 14).
- Use semantic HTML (`<main>`, `<nav>`, `<section>`, `<button>`, not `<div>` for everything).

---

## File-by-File Implementation Guide

### `models.py`
- Define `Base = DeclarativeBase()`.
- `Recipe` model with columns from ARCHITECTURE.md §3.
- `get_engine()` creates `create_engine("sqlite:///./recipes.db", ...)` with `connect_args={"check_same_thread": False}` and WAL mode pragma.
- `get_session()` returns a `sessionmaker` context manager.
- `init_db()` calls `Base.metadata.create_all(engine)`.
- **This file has zero side effects when imported** — call `init_db()` explicitly from `app.py` and `bot.py` at startup.

### `import_csv.py`
- Read `my_food_reels.csv` (single column: `URL`, header on row 1).
- Skip rows where the URL doesn't match the Instagram regex (e.g., bare `https://www.instagram.com/reels/`).
- Extract shortcode with: `re.search(r'instagram\.com/(?:p|reels)/([A-Za-z0-9_-]+)', url)`.
- Use `session.merge()` or check-before-insert to avoid duplicates (URL is UNIQUE).
- Print a summary: `Added: X, Skipped (duplicate): Y, Skipped (invalid): Z`.

### `bot.py`
- Load `.env` at top.
- Guard: `if update.effective_user.id != AUTHORIZED_USER_ID: return`
- URL regex: `r'https?://(?:www\.)?instagram\.com/(?:p|reels)/[A-Za-z0-9_-]+/?'`
- Extract the first match from the message text.
- All DB operations in a `with get_session() as session:` block.
- Use `python-telegram-bot` v20+ Application pattern (not old Updater pattern):
  ```python
  app = ApplicationBuilder().token(TG_TOKEN).build()
  app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
  app.run_polling()
  ```

### `app.py`
- Use `FastAPI` with `Jinja2Templates(directory="templates")`.
- Mount `StaticFiles(directory="static")` at `/static`.
- Session cookie: use `itsdangerous.URLSafeTimedSerializer` with `SECRET_KEY`.
  - Sign on login: `serializer.dumps({"authed": True})`.
  - Verify: `serializer.loads(cookie, max_age=30*24*3600)`.
  - Wrap auth check in a dependency `get_current_user()` that raises `RedirectResponse("/login")` if invalid.
- `/api/spin`: use `func.random()` from `sqlalchemy` for SQLite-compatible random ordering.
- `/api/recipe/{id}` (PATCH): accept JSON body `{"category": "...", "mood": "..."}`. Validate against allowlists. Return updated recipe.
- Call `init_db()` inside a `lifespan` context manager on startup.

### `templates/base.html`
- Include Tailwind CDN: `<script src="https://cdn.tailwindcss.com"></script>`
- Include Google Fonts (Inter).
- Define Tailwind config in a `<script>` block extending the theme with the warm palette (see ARCHITECTURE.md §7).
- `{% block content %}{% endblock %}` in `<main>`.

### `templates/index.html`
- Filter chips: each chip toggles an `active` CSS class and updates a JS state object `filters = {category: null, mood: null}`.
- Spin button: calls `GET /api/spin?category=X&mood=Y`, handles "no results" gracefully (show a message, not an error).
- Recipe reveal: hidden `<div>` that fades in with the returned recipe's category + mood + "Let's Cook!" button.
- "Let's Cook!" button calls `openRecipe(url)` from `app.js`.

### `templates/manage.html`
- Render a list of all recipes server-side via Jinja2 (pass `recipes` list from FastAPI route).
- "Edit" button opens a modal pre-filled with current category/mood.
- Modal submits via `fetch PATCH /api/recipe/{id}` and updates the row in-place on success.

### `static/app.js`
Key functions to implement:
```javascript
// Deep link with fallback
function openRecipe(url) { ... }

// Spin the roulette
async function spin() { ... }

// Update recipe metadata
async function saveEdit(id, category, mood) { ... }

// Toast notification helper
function showToast(message, type = 'success') { ... }

// Filter chip toggle
function toggleFilter(type, value, el) { ... }
```

---

## Environment Setup

```bash
# Windows (PowerShell) — create venv
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Install deps
pip install -r requirements.txt
```

**Get your Telegram User ID:**
1. Send any message to `@userinfobot` on Telegram.
2. It replies with your numeric User ID. Put that in `.env` as `AUTHORIZED_USER_ID`.

**Get a Telegram Bot Token:**
1. Message `@BotFather` on Telegram.
2. `/newbot` → follow prompts → copy the token to `.env` as `TG_TOKEN`.

---

## Common Pitfalls & Solutions

| Problem | Solution |
|---------|----------|
| `check_same_thread` SQLite error | Set `connect_args={"check_same_thread": False}` in `create_engine` |
| Bot and web server DB conflicts | Enable WAL mode: `engine.execute("PRAGMA journal_mode=WAL")` on connect |
| `itsdangerous` token expired | Catch `SignatureExpired` and `BadSignature`, redirect to `/login` |
| Instagram URL with query params | Strip query string before storing: `url.split('?')[0]` |
| PTB v20 vs v13 confusion | Always use `ApplicationBuilder`, not `Updater`. No `@bot.message_handler` decorators. |
| Tailwind CDN purge in prod | For v1 (private use), CDN is fine. For prod, set up a proper Tailwind build. |
| FastAPI form data | Must install `python-multipart` for `Form(...)` to work |

---

## Testing Checklist (run before marking a phase complete)

### Phase 1 (DB)
- [ ] `python -c "from models import init_db; init_db()"` — no errors
- [ ] `python import_csv.py` — prints "Added: 95, Skipped (invalid): 1"

### Phase 2 (Bot)
- [ ] `python bot.py` starts without errors
- [ ] Sending an Instagram link from the authorized account adds to DB
- [ ] Sending same link again returns "Already in the collection!"
- [ ] Sending from a different account is silently ignored

### Phase 3 (Web)
- [ ] `uvicorn app:app --reload` starts without errors
- [ ] `/login` renders, wrong password shows error, correct password redirects to `/`
- [ ] `/api/spin` returns JSON with all 5 fields
- [ ] `/api/spin?category=Pasta` only returns Pasta recipes (or 404 if none)
- [ ] `PATCH /api/recipe/1` with valid body updates the DB
- [ ] Accessing `/` without cookie redirects to `/login`

### Phase 4 (UI)
- [ ] Mobile view (375px): no horizontal overflow
- [ ] Spin animation works, card reveals smoothly
- [ ] "Let's Cook!" attempts Instagram deep link then falls back
- [ ] Edit modal saves and updates the row without page reload

---

## Agent Workflow Template

When resuming work as an agent on this project:

```
1. Read PLAN.md → identify next ⬜ task
2. Read ARCHITECTURE.md §{relevant section}
3. Read existing code files that will be touched
4. Implement the task
5. Mark task ✅ in PLAN.md
6. Briefly note any decisions made in the "Decisions Log" section of PLAN.md
```

Do not implement multiple phases in one go without checking in. Implement one Phase at a time and let the developer verify before continuing.
