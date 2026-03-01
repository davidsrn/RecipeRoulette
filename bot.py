"""
bot.py — Telegram bot that listens for Instagram links and saves them to the DB.

Run:
    python bot.py

Requires in .env:
    TG_TOKEN            — Bot token from @BotFather
    AUTHORIZED_USER_ID  — Your numeric Telegram user ID (from @userinfobot)
"""

import logging
import os
import re

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from models import Recipe, get_session, init_db

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN", "")
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID", "0"))

# ── Regexes ───────────────────────────────────────────────────────────────────

# Matches full Instagram reel / post URLs
INSTA_URL_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:p|reels?)/[A-Za-z0-9_-]+/?"
)

# Extracts the shortcode from an Instagram URL
SHORTCODE_RE = re.compile(
    r"instagram\.com/(?:p|reels?)/([A-Za-z0-9_-]+)"
)

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────


def extract_instagram_url(text: str) -> str | None:
    """Return the first Instagram URL found in text, or None."""
    m = INSTA_URL_RE.search(text)
    return m.group(0).rstrip("/") if m else None


def extract_shortcode(url: str) -> str | None:
    m = SHORTCODE_RE.search(url)
    return m.group(1) if m else None


def clean_url(url: str) -> str:
    """Strip query strings for a canonical URL."""
    return url.split("?")[0].rstrip("/")


async def fetch_og_title(url: str) -> str | None:
    """Try to fetch the og:title from an Instagram URL. Returns None on failure."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=6.0) as client:
            r = await client.get(url, headers={
                "User-Agent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
                )
            })
        # Try both attribute orderings for the og:title meta tag
        m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', r.text)
        if not m:
            m = re.search(r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:title["\']', r.text)
        return m.group(1).strip() if m else None
    except Exception:
        return None


# ── Handler ───────────────────────────────────────────────────────────────────


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Ignore messages from anyone other than the authorized user
    if not update.effective_user or update.effective_user.id != AUTHORIZED_USER_ID:
        return

    text = update.message.text or ""
    raw_url = extract_instagram_url(text)

    if not raw_url:
        # Not an Instagram link — silently ignore
        return

    url = clean_url(raw_url)
    shortcode = extract_shortcode(url)

    if not shortcode:
        await update.message.reply_text("Hmm, couldn't parse that Instagram link.")
        return

    with get_session() as session:
        existing = session.query(Recipe).filter_by(url=url).first()

        if existing:
            await update.message.reply_text("Already in the collection!")
            logger.info("Duplicate skipped: %s", url)
            return

        session.add(Recipe(url=url, shortcode=shortcode))
        session.commit()

    # Best-effort title fetch (runs after replying so it doesn't delay the response)
    await update.message.reply_text("Recipe added to the Roulette! \U0001f35d")
    logger.info("Added: %s (shortcode: %s)", url, shortcode)

    title = await fetch_og_title(url)
    if title:
        with get_session() as session:
            recipe = session.query(Recipe).filter_by(url=url).first()
            if recipe:
                recipe.title = title
                session.commit()
        logger.info("Title fetched: %s", title)


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    if not TG_TOKEN:
        raise RuntimeError("TG_TOKEN is not set in .env")
    if not AUTHORIZED_USER_ID:
        raise RuntimeError("AUTHORIZED_USER_ID is not set in .env")

    init_db()
    logger.info("DB ready. Starting bot (polling)...")

    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running. Authorized user ID: %d", AUTHORIZED_USER_ID)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
