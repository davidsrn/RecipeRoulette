"""
backfill_thumbnails.py — One-time script to fetch og:image (and og:title if missing)
for all existing recipes that don't have a thumbnail_url stored yet.

Usage:
    python backfill_thumbnails.py               # dry run (no writes)
    python backfill_thumbnails.py --write        # actually update the DB
    python backfill_thumbnails.py --write --delay 1.5  # slow down requests (seconds between each)
"""

import argparse
import asyncio
import re

import httpx

from models import Recipe, get_session, init_db

UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


async def fetch_og_metadata(client: httpx.AsyncClient, url: str) -> tuple[str | None, str | None]:
    """Return (og:title, og:image) for the given URL, or (None, None) on failure."""
    try:
        r = await client.get(url, headers={"User-Agent": UA})
        html = r.text

        m_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', html)
        if not m_title:
            m_title = re.search(r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:title["\']', html)

        m_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']', html)
        if not m_img:
            m_img = re.search(r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:image["\']', html)

        title = m_title.group(1).strip() if m_title else None
        thumbnail_url = m_img.group(1).strip() if m_img else None
        return title, thumbnail_url
    except Exception as exc:
        return None, None


async def backfill(write: bool, delay: float) -> None:
    init_db()

    with get_session() as session:
        recipes = session.query(Recipe).filter(Recipe.thumbnail_url.is_(None)).all()
        total = len(recipes)

    if total == 0:
        print("All recipes already have thumbnails. Nothing to do.")
        return

    mode = "WRITE" if write else "DRY RUN"
    print(f"[{mode}] Found {total} recipes without a thumbnail.\n")

    fetched = skipped = failed = 0

    async with httpx.AsyncClient(follow_redirects=True, timeout=8.0) as client:
        for i, recipe in enumerate(recipes, 1):
            prefix = f"[{i:3}/{total}]"
            og_title, og_image = await fetch_og_metadata(client, recipe.url)

            if not og_image:
                print(f"{prefix} FAIL  no og:image  {recipe.shortcode}")
                failed += 1
            else:
                short_img = og_image[:60] + "..." if len(og_image) > 60 else og_image
                print(f"{prefix} OK    {recipe.shortcode}  -> {short_img}")
                if write:
                    with get_session() as session:
                        r = session.get(Recipe, recipe.id)
                        if r:
                            r.thumbnail_url = og_image
                            if og_title and not r.title:
                                r.title = og_title
                            session.commit()
                fetched += 1

            if delay > 0 and i < total:
                await asyncio.sleep(delay)

    print(f"\nDone. fetched={fetched}  failed={failed}  total={total}")
    if not write:
        print("(dry run — re-run with --write to save changes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill thumbnail_url for existing recipes.")
    parser.add_argument("--write", action="store_true", help="Actually write to the DB (default: dry run)")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between requests (default: 0.5)")
    args = parser.parse_args()

    asyncio.run(backfill(write=args.write, delay=args.delay))
