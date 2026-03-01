# RecipeRoulette — System Architecture

> Version: 1.0 · Date: 2026-03-01

---

## 1. High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRIVATE NETWORK / LOCAL                  │
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────┐  │
│  │ Telegram App │────▶│  bot.py      │────▶│                │  │
│  │ (Phone)      │◀────│  (Async PTB) │     │  SQLite DB     │  │
│  └──────────────┘     └──────────────┘     │  (recipes.db)  │  │
│                                            │                │  │
│  ┌──────────────┐     ┌──────────────┐     │  SQLAlchemy    │  │
│  │ Browser      │────▶│  app.py      │────▶│  ORM          │  │
│  │ (iPhone/     │◀────│  (FastAPI)   │     │                │  │
│  │  Android)    │     └──────────────┘     └────────────────┘  │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

The two processes (bot + web server) share the **same SQLite file**. They can run concurrently because SQLite handles concurrent reads well, and writes are infrequent.

---

## 2. Directory Structure

```
/RecipeRoulette
├── app.py                  # FastAPI web server
├── bot.py                  # Telegram bot (async polling)
├── models.py               # SQLAlchemy models + DB init
├── import_csv.py           # One-time CSV import utility
├── requirements.txt        # Python dependencies
├── .env                    # Secrets (never commit)
├── .env.example            # Template for .env
├── recipes.db              # SQLite database (gitignored)
├── my_food_reels.csv       # Source data (96 URLs)
│
├── templates/
│   ├── base.html           # Shared layout, Tailwind, fonts
│   ├── login.html          # Password gate
│   ├── index.html          # Roulette + filter UI
│   └── manage.html         # Management list + edit modal
│
├── static/
│   ├── app.js              # All client-side JS
│   └── style.css           # Custom CSS overrides (minimal)
│
├── PLAN.md                 # Implementation tracker
├── ARCHITECTURE.md         # This file
└── DEVELOPMENT.md          # Dev instructions
```

---

## 3. Database Schema

### Table: `recipes`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `url` | VARCHAR | UNIQUE, NOT NULL | Full Instagram URL |
| `shortcode` | VARCHAR | NOT NULL | Extracted from URL path |
| `category` | VARCHAR | DEFAULT "Uncategorized" | Pasta, Chicken, Dessert… |
| `mood` | VARCHAR | DEFAULT "None" | Quick, Date Night, Healthy… |
| `date_added` | DATETIME | DEFAULT now() | UTC timestamp |

### Shortcode Extraction
- `/p/{shortcode}/` → extract group 1
- `/reels/{shortcode}/` → extract group 1
- Regex: `instagram\.com/(?:p|reels)/([A-Za-z0-9_-]+)`

### Predefined Categories (editable in code)
```
Uncategorized, Pasta, Chicken, Beef, Seafood, Vegetarian,
Dessert, Breakfast, Soup, Salad, Snack, Other
```

### Predefined Moods (editable in code)
```
None, Quick, Date Night, Healthy, Comfort Food,
Fancy, Lazy Day, Meal Prep
```

---

## 4. Backend: `models.py`

```
models.py
  ├── Base (SQLAlchemy DeclarativeBase)
  ├── Recipe (ORM model)
  ├── get_engine()    → creates SQLite engine
  ├── get_session()   → session factory
  └── init_db()       → creates tables if not exist
```

Used by both `app.py` and `bot.py`. Single shared engine, SQLite WAL mode enabled for concurrent access.

---

## 5. Backend: `bot.py`

```
Startup
  └── ApplicationBuilder(TG_TOKEN).build()
        └── add_handler(MessageHandler(filters.TEXT, handle_message))
              └── handle_message()
                    ├── Guard: message.from_user.id == AUTHORIZED_USER_ID
                    ├── Extract Instagram URL with regex
                    ├── Extract shortcode from URL
                    ├── DB lookup by url (check duplicate)
                    ├── If duplicate → reply "Already in the collection!"
                    └── If new → INSERT + reply "Recipe added! 🍝"
```

**Process model:** runs as a standalone long-polling process. Can be started independently of the web server.

---

## 6. Backend: `app.py`

### Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/login` | Public | Login page |
| POST | `/login` | Public | Validates password, sets cookie |
| POST | `/logout` | Authed | Clears session cookie |
| GET | `/` | Authed | Roulette main page |
| GET | `/api/spin` | Authed | Returns random recipe JSON |
| GET | `/manage` | Authed | Management list page |
| PATCH | `/api/recipe/{id}` | Authed | Update category/mood |
| GET | `/api/categories` | Authed | Returns category list |
| GET | `/api/moods` | Authed | Returns mood list |

### Auth Mechanism
1. POST `/login` with `password` form field
2. Compare against `APP_PASSWORD` from `.env`
3. On match: create signed cookie with `itsdangerous.URLSafeTimedSerializer`
4. Cookie name: `rr_session` · Max age: 30 days
5. All protected routes check cookie signature before responding
6. Invalid/expired cookie → redirect to `/login`

### `/api/spin` Logic
```
GET /api/spin?category=Pasta&mood=Quick
  ├── Parse optional query params (category, mood)
  ├── Build SQLAlchemy query with filters
  ├── ORDER BY RANDOM() LIMIT 1
  └── Return JSON { id, url, shortcode, category, mood }
```

---

## 7. Frontend Architecture

### Pages

**`/` (index.html) — Roulette**
```
Header (Logo + nav link to /manage)
Filter Bar
  ├── Category chips (horizontal scroll)
  └── Mood chips (horizontal scroll)
Spin Button (large, centered, animated)
Recipe Reveal Card (hidden until spin)
  ├── Category badge
  ├── Mood badge
  ├── "Let's Cook!" button  ← deep link
  └── "Spin Again" button
```

**`/manage` (manage.html) — Management**
```
Header + search/filter bar
Recipe List
  └── Each row: shortcode preview, category, mood, [Edit] button
Edit Modal (vanilla JS)
  ├── Category <select>
  ├── Mood <select>
  └── Save → PATCH /api/recipe/{id}
```

**`/login` (login.html) — Auth Gate**
```
Centered card
  ├── App logo/name
  ├── Password <input type="password">
  └── Submit button
```

### Design System

| Token | Value |
|-------|-------|
| Primary | `#F97316` (orange-500) |
| Primary Dark | `#EA580C` (orange-600) |
| Accent | `#FBBF24` (amber-400) |
| Background | `#FFFBF5` (warm white) |
| Surface | `#FFFFFF` |
| Text Primary | `#1C1917` (stone-900) |
| Text Muted | `#78716C` (stone-500) |
| Border | `#E7E5E4` (stone-200) |
| Font | System UI → `Inter` via Google Fonts |

### Deep Link Logic (`app.js`)
```javascript
function openRecipe(url) {
  const shortcode = extractShortcode(url);
  const instagramApp = `instagram://media?id=${shortcode}`;

  // Try app deep link; fall back to HTTPS after 500ms
  window.location = instagramApp;
  setTimeout(() => { window.open(url, '_blank'); }, 500);
}
```

---

## 8. Environment Variables (`.env`)

```bash
# Telegram
TG_TOKEN=your_bot_token_here
AUTHORIZED_USER_ID=123456789   # Your Telegram numeric user ID

# Web App
APP_PASSWORD=your_password_here
SECRET_KEY=random_32char_string  # For cookie signing

# Optional
DB_PATH=./recipes.db             # Default if not set
```

---

## 9. Dependencies (`requirements.txt`)

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
jinja2>=3.1.0
python-multipart>=0.0.9        # Form parsing in FastAPI
sqlalchemy>=2.0.0
python-telegram-bot>=20.0      # Async PTB v20+
python-dotenv>=1.0.0
itsdangerous>=2.1.0            # Cookie signing
```

---

## 10. Running the App

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Copy and fill .env
cp .env.example .env

# 3. Import existing CSV (one-time)
python import_csv.py

# 4. Start web server (Terminal 1)
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 5. Start Telegram bot (Terminal 2)
python bot.py
```

Access the web app at `http://localhost:8000` (or your machine's local IP on mobile).

---

## 11. Security Considerations

- **Auth:** Cookie is HMAC-signed with `SECRET_KEY`. Tampering invalidates it.
- **Bot:** Hard-coded `AUTHORIZED_USER_ID` guard. No other user can add recipes.
- **No HTTPS locally:** For LAN use this is acceptable. If exposed to internet, add a reverse proxy (nginx + Let's Encrypt) or use Tailscale.
- **SQLite WAL mode:** Enabled to prevent lock contention between bot writes and web reads.
- **No user input sanitization risks:** URL is extracted via regex, category/mood are validated against an allowlist on the server side.

---

## 12. Future Enhancements (Out of Scope for v1)

- Thumbnail fetching (Instagram oEmbed API or scraping)
- Multiple users / households
- "Cooked it!" button to track history
- PWA manifest for "Add to Home Screen"
- Webhook mode for Telegram bot (requires HTTPS endpoint)
