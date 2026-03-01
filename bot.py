"""
bot.py — Telegram bot that listens for Instagram links and saves them to the DB.

Run:
    python bot.py

Requires in .env:
    TG_TOKEN            — Bot token from @BotFather
    AUTHORIZED_USER_ID  — Your numeric Telegram user ID (from @userinfobot)
"""

import html as _html
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

_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
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


def clean_og_title(raw: str | None) -> str | None:
    """Decode HTML entities and strip the 'Author on Instagram:' prefix."""
    if not raw:
        return None
    text = _html.unescape(raw)
    if " on Instagram: " in text:
        text = text.split(" on Instagram: ", 1)[1]
    text = text.strip('"').strip("'").strip()
    return text or None


async def fetch_og_metadata(url: str) -> tuple[str | None, bytes | None, str | None]:
    """Fetch title, thumbnail bytes, and post description from an Instagram URL.

    All fetched in one httpx session so the CDN image URL (IP/session-bound)
    is requested before it expires.
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            r = await client.get(url, headers={"User-Agent": _UA})
            html_text = r.text

            def _og(prop: str) -> str | None:
                m = re.search(
                    rf'<meta[^>]+property=["\']og:{prop}["\'][^>]+content=["\'](.*?)["\']',
                    html_text,
                )
                if not m:
                    m = re.search(
                        rf'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:{prop}["\']',
                        html_text,
                    )
                return _html.unescape(m.group(1)).strip() if m else None

            title = clean_og_title(_og("title"))
            description = _og("description") or None

            # Download thumbnail bytes in the same session (CDN URL is IP-bound)
            image_bytes: bytes | None = None
            img_url = _og("image")
            if img_url:
                img_r = await client.get(img_url, headers={"User-Agent": _UA})
                if img_r.status_code == 200:
                    image_bytes = img_r.content

        return title, image_bytes, description
    except Exception:
        return None, None, None


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

    # Best-effort metadata fetch (runs after replying so it doesn't delay the response)
    await update.message.reply_text("Recipe added to the Roulette! \U0001f35d")
    logger.info("Added: %s (shortcode: %s)", url, shortcode)

    title, image_bytes, description = await fetch_og_metadata(url)
    if title or image_bytes or description:
        with get_session() as session:
            recipe = session.query(Recipe).filter_by(url=url).first()
            if recipe:
                if title:
                    recipe.title = title
                if image_bytes:
                    recipe.thumbnail_data = image_bytes
                if description:
                    recipe.description = description
                session.commit()
        logger.info(
            "Metadata saved — title: %s, thumbnail: %s bytes, description: %s chars",
            title,
            len(image_bytes) if image_bytes else 0,
            len(description) if description else 0,
        )


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
