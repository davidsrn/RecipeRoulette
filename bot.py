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

    await update.message.reply_text("Recipe added to the Roulette! \U0001f35d")
    logger.info("Added: %s (shortcode: %s)", url, shortcode)


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
