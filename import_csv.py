"""
import_csv.py — One-time utility to seed the DB from my_food_reels.csv.

Usage:
    python import_csv.py
    python import_csv.py --csv path/to/other.csv
"""

import argparse
import csv
import re
import sys
from pathlib import Path

from models import Recipe, get_session, init_db

# Matches both /p/ and /reels/ Instagram URLs
URL_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:p|reels)/([A-Za-z0-9_-]+)"
)


def extract_shortcode(url: str) -> str | None:
    m = URL_RE.search(url)
    return m.group(1) if m else None


def clean_url(url: str) -> str:
    """Strip query strings and trailing slashes for a canonical URL."""
    return url.split("?")[0].rstrip("/")


def import_csv(csv_path: Path) -> None:
    init_db()

    added = skipped_dup = skipped_invalid = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "URL" not in (reader.fieldnames or []):
            print("ERROR: CSV must have a 'URL' column header.")
            sys.exit(1)

        with get_session() as session:
            for row in reader:
                raw_url = (row.get("URL") or "").strip()
                if not raw_url:
                    skipped_invalid += 1
                    continue

                url = clean_url(raw_url)
                shortcode = extract_shortcode(url)

                if not shortcode:
                    print(f"  SKIP (invalid): {raw_url}")
                    skipped_invalid += 1
                    continue

                # Check for duplicate
                existing = session.query(Recipe).filter_by(url=url).first()
                if existing:
                    skipped_dup += 1
                    continue

                session.add(Recipe(url=url, shortcode=shortcode))
                added += 1

            session.commit()

    total = added + skipped_dup + skipped_invalid
    print(f"\nImport complete -- {total} rows processed:")
    print(f"  Added:              {added}")
    print(f"  Skipped (duplicate): {skipped_dup}")
    print(f"  Skipped (invalid):   {skipped_invalid}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import food reels from CSV into DB.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("my_food_reels.csv"),
        help="Path to the CSV file (default: my_food_reels.csv)",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"ERROR: File not found: {args.csv}")
        sys.exit(1)

    print(f"Importing from: {args.csv}")
    import_csv(args.csv)

