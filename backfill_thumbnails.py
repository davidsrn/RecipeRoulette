"""
backfill_thumbnails.py — Populate thumbnail_data (image bytes) and clean titles
for existing recipes that are missing them.

Usage:
    python backfill_thumbnails.py               # dry run (no writes)
    python backfill_thumbnails.py --write        # write to DB
    python backfill_thumbnails.py --write --delay 1.0   # slow down (seconds between requests)
    python backfill_thumbnails.py --write --retitle      # also overwrite dirty existing titles
"""

import argparse
import asyncio

from bot import fetch_og_metadata
from models import Recipe, get_session, init_db


async def backfill(write: bool, delay: float, retitle: bool) -> None:
    init_db()

    with get_session() as session:
        if retitle:
            recipes = session.query(Recipe).all()
        else:
            recipes = session.query(Recipe).filter(Recipe.thumbnail_data.is_(None)).all()
        total = len(recipes)

    if total == 0:
        print("Nothing to do.")
        return

    mode = "WRITE" if write else "DRY RUN"
    flag = "+retitle" if retitle else ""
    print(f"[{mode}{flag}] {total} recipes to process.\n")

    ok = skipped = failed = 0

    for i, recipe in enumerate(recipes, 1):
        prefix = f"[{i:3}/{total}]"
        title, image_bytes = await fetch_og_metadata(recipe.url)

        if not image_bytes and not title:
            print(f"{prefix} FAIL  {recipe.shortcode}")
            failed += 1
        else:
            thumb_kb = f"{len(image_bytes) // 1024}KB" if image_bytes else "no-img"
            title_display = repr(title)[:40].encode("ascii", errors="replace").decode("ascii")
            print(f"{prefix} OK    {recipe.shortcode}  title={title_display}  thumb={thumb_kb}")

            if write:
                with get_session() as session:
                    r = session.get(Recipe, recipe.id)
                    if r:
                        if image_bytes and not r.thumbnail_data:
                            r.thumbnail_data = image_bytes
                        if title and (retitle or not r.title):
                            r.title = title
                        session.commit()
            ok += 1

        if delay > 0 and i < total:
            await asyncio.sleep(delay)

    print(f"\nDone. ok={ok}  failed={failed}  total={total}")
    if not write:
        print("(dry run — re-run with --write to save changes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill thumbnail_data and titles.")
    parser.add_argument("--write", action="store_true", help="Write to DB (default: dry run)")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between requests (default: 0.5)")
    parser.add_argument("--retitle", action="store_true", help="Re-fetch and overwrite existing titles too")
    args = parser.parse_args()

    asyncio.run(backfill(write=args.write, delay=args.delay, retitle=args.retitle))
