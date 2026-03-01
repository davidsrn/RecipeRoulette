# RecipeRoulette 🍽️

A private web app for saving Instagram food reels via Telegram and spinning a random one to decide what to cook.

---

## Running Locally

```bash
# 1. Create and fill .env
cp .env.example .env
# edit .env with your values

# 2. Install dependencies
python -m venv venv
./venv/Scripts/activate       # Windows Git Bash
source venv/bin/activate      # macOS / Linux

pip install -r requirements.txt

# 3. Import existing recipes (first run only)
python import_csv.py

# 4. Start web server  (Terminal 1)
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 5. Start Telegram bot (Terminal 2)
python bot.py
```

Open `http://localhost:8000` in your browser.

---

## Deploying to Railway

### Prerequisites
- A [Railway](https://railway.com) account
- Your repo pushed to GitHub

### Step 1 — Create a new project
1. Go to Railway dashboard → **New Project** → **Deploy from GitHub repo**
2. Select this repository

### Step 2 — Attach a persistent volume (keeps your DB across deploys)
1. In your service → **Settings** → **Volumes**
2. Add a volume, mount path: `/data`

### Step 3 — Set environment variables
In your service → **Variables**, add:

| Variable | Value |
|----------|-------|
| `TG_TOKEN` | Your Telegram bot token |
| `AUTHORIZED_USER_ID` | Your Telegram numeric user ID |
| `APP_PASSWORD` | Your chosen web app password |
| `SECRET_KEY` | A random 32-char string (run: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DB_PATH` | `/data/recipes.db` |

### Step 4 — Deploy
Railway will auto-build using the `Dockerfile` and run `start.sh`.

On **first boot**, the startup script detects no DB at `/data/recipes.db`, imports `my_food_reels.csv` automatically, then starts both the web server and Telegram bot.

### Step 5 — Get your URL
Railway assigns a public URL like `https://your-app.up.railway.app`.
Open it in your browser — it will redirect to the login page.

---

## Project Structure

```
├── app.py              Web server (FastAPI)
├── bot.py              Telegram bot
├── models.py           SQLAlchemy DB models
├── import_csv.py       One-time CSV import utility
├── start.sh            Docker entrypoint (runs both services)
├── Dockerfile          Container image definition
├── railway.toml        Railway deployment config
├── requirements.txt    Python dependencies
├── .env.example        Environment variable template
├── templates/          Jinja2 HTML templates
└── static/             CSS + JavaScript
```

---

## Telegram Bot Usage

Send any Instagram link to your bot — it handles both formats:
- `https://www.instagram.com/p/SHORTCODE/`
- `https://www.instagram.com/reels/SHORTCODE/`

The bot replies:
- **"Already in the collection!"** — URL was previously saved
- **"Recipe added to the Roulette! 🍝"** — saved successfully
