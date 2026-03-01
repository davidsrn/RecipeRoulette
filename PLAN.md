# RecipeRoulette — Implementation Plan & Progress Tracker

> Last updated: 2026-03-01 (Phases 0–6 complete — ready to deploy on Railway)
> Status legend: ⬜ Pending · 🔄 In Progress · ✅ Done · ❌ Blocked

---

## Phase 0 — Project Setup
| # | Task | Status | Notes |
|---|------|--------|-------|
| 0.1 | Create project directory structure | ✅ | `templates/`, `static/` created |
| 0.2 | Create `.env` template | ✅ | `.env.example` created |
| 0.3 | Create `requirements.txt` | ✅ | venv created, all deps installed |
| 0.4 | Verify CSV import data | ✅ | 96 valid URLs in my_food_reels.csv |

---

## Phase 1 — Database Layer (`models.py`)
| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Define `Recipe` SQLAlchemy model | ✅ | id, url, shortcode, category, mood, date_added |
| 1.2 | Create DB init / migration helper | ✅ | `init_db()`, WAL mode enabled |
| 1.3 | Write `import_csv.py` utility | ✅ | 96 added, 1 invalid skipped — verified |

---

## Phase 2 — Telegram Bot (`bot.py`)
| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Bot scaffolding with `python-telegram-bot` async | ✅ | ApplicationBuilder pattern, PTB v20+ |
| 2.2 | Instagram URL detection (reels + /p/ patterns) | ✅ | Regex covers /p/, /reels/, /reel/ |
| 2.3 | Shortcode extraction from URL | ✅ | SHORTCODE_RE group 1 |
| 2.4 | Duplicate check + DB save | ✅ | filter_by(url=url), session.commit() |
| 2.5 | AUTHORIZED_USER_ID guard | ✅ | Returns silently if user ID doesn't match |
| 2.6 | Reply messages ("Already in collection!" / "Recipe added! 🍝") | ✅ | Emoji via unicode escape (cp1252 safe) |

---

## Phase 3 — Web Application (`app.py`)
| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | FastAPI scaffold + Jinja2 templates | ✅ | Static files mounted at /static |
| 3.2 | Auth gate — password login page | ✅ | POST /login, itsdangerous signed cookie |
| 3.3 | Auth middleware — cookie validation | ✅ | verify_session_cookie() on every route |
| 3.4 | `GET /` — main roulette page | ✅ | Categories + moods passed via template context |
| 3.5 | `GET /api/spin` — random recipe endpoint | ✅ | func.random(), optional filter params |
| 3.6 | `GET /manage` — management list page | ✅ | Server-side rendered list, desc date order |
| 3.7 | `PATCH /api/recipe/{id}` — edit category/mood | ✅ | Allowlist validation, returns updated recipe |
| 3.8 | Deep link logic for Instagram | ✅ | In app.js: instagram:// with HTTPS fallback |
| 3.9 | `POST /logout` — clear session cookie | ✅ | delete_cookie(COOKIE_NAME) |

---

## Phase 4 — Frontend (`templates/` + `static/`)
| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | `base.html` — Tailwind CDN, warm palette, mobile-first | ✅ | Sticky nav, Inter font, warm tokens |
| 4.2 | `login.html` — password input page | ✅ | Standalone (no base.html for clean layout) |
| 4.3 | `index.html` — roulette + filter UI | ✅ | Category + mood chips, spin button |
| 4.4 | Recipe reveal card — show Type + Mood before URL | ✅ | Gradient card with fade-up animation |
| 4.5 | "Let's Cook!" button with deep link | ✅ | openRecipe() in app.js |
| 4.6 | `manage.html` — list view with Edit inline | ✅ | Live search filter, open-in-Instagram link |
| 4.7 | Edit modal — category/mood dropdowns | ✅ | Bottom-sheet modal, in-place row update |
| 4.8 | `static/app.js` — all JS logic | ✅ | spin, openRecipe, toggleFilter, saveEdit, toast |

---

## Phase 5 — Integration & Testing
| # | Task | Status | Notes |
|---|------|--------|-------|
| 5.1 | Run CSV import successfully | ✅ | 96 added, 1 invalid skipped |
| 5.2 | Test Telegram bot end-to-end | ✅ | Duplicate detected + new URL saved — verified on device |
| 5.3 | Test web auth flow | ✅ | Login 200, wrong pw 401, cookie set, logout clears |
| 5.4 | Test spin with filters | ✅ | /api/spin returns JSON; reveal card animates correctly |
| 5.5 | Test edit (category/mood update) | ✅ | PATCH 200, row updates in-place, "Saved!" toast shown |
| 5.6 | Mobile browser smoke test | ✅ | Verified at 390×844 (iPhone 14 size) — no overflow |

---

## Phase 6 — Deployment (Docker)
| # | Task | Status | Notes |
|---|------|--------|-------|
| 6.1 | Write `Dockerfile` | ✅ | Multi-stage build; CRLF fix for Windows line endings |
| 6.2 | Write `start.sh` entrypoint | ✅ | Auto-imports CSV on first boot; runs web + bot |
| 6.3 | Write `.dockerignore` | ✅ | Excludes venv, .env, recipes.db, __pycache__ |
| 6.4 | Write `railway.toml` | ✅ | dockerfile builder, always-restart policy |
| 6.5 | Write `README.md` with deploy instructions | ✅ | Local + Railway step-by-step |
| 6.6 | Test `docker build` locally | ⬜ | Docker not installed on dev machine — test via Railway |

---

## Known Issues / Decisions Log
| Date | Item | Decision |
|------|------|----------|
| 2026-03-01 | CSV row 2 is `https://www.instagram.com/reels/` (no shortcode) | `import_csv.py` must skip invalid URLs |
| 2026-03-01 | Framework choice | FastAPI chosen (async-native, great for bot+web co-existence) |
| 2026-03-01 | Auth method | Simple password → signed cookie (itsdangerous) |
| 2026-03-01 | Bot polling vs webhook | Polling for simplicity; can switch to webhook later |
| 2026-03-01 | Windows terminal emoji | Print statements in import_csv.py use ASCII only (cp1252 limitation) |
| 2026-03-01 | venv location | `./venv/` inside project root; activate with `./venv/Scripts/activate` (Windows) |
