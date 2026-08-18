"""
One-time importer for the practice problem bank.

WHY A SCRIPT AND NOT A LIVE FETCH: LeetCode's GraphQL API is private and
their Terms of Service prohibit scraping/redistributing problem content,
which is also their copyrighted material. Instead this imports from a
PUBLIC, redistributable LeetCode dataset (e.g. the ones published on
Kaggle) that you download yourself as a CSV. Because the import is static,
there's no weekly sync job and no response cache to keep coherent -- the
data doesn't change under us.

USAGE:
    1. Download a LeetCode problems dataset CSV from Kaggle.
    2. python scripts/import_practice_problems.py path/to/leetcode.csv

The CSV needs columns for title, slug, difficulty, and description. Column
names vary between datasets, so COLUMN_ALIASES below maps the common
variants -- add to it if your CSV uses different headers.

Re-running is safe: rows are matched on title_slug and skipped if already
present, so a partial import can be resumed by just running it again.
"""

import csv
import json
import os
import sys

import psycopg

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings  # noqa: E402

COLUMN_ALIASES = {
    "title": ["title", "name", "question_title"],
    "title_slug": ["title_slug", "slug", "titleSlug", "question_slug"],
    "difficulty": ["difficulty", "level"],
    "description": ["description", "content", "question_content", "problem_statement"],
    "topic_tags": ["topic_tags", "tags", "related_topics", "topics"],
}

DIFFICULTY_MAP = {
    "1": "easy", "2": "medium", "3": "hard",
    "easy": "easy", "medium": "medium", "hard": "hard",
}


def _pick(row: dict, field: str) -> str | None:
    for alias in COLUMN_ALIASES[field]:
        if alias in row and row[alias]:
            return row[alias]
    return None


def _slugify(title: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in title.lower()).strip("-")


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    for sep in (",", ";", "|"):
        if sep in raw:
            return [t.strip().lower().replace(" ", "-") for t in raw.split(sep) if t.strip()]
    return [raw.strip().lower().replace(" ", "-")]


def import_csv(csv_path: str) -> None:
    conn = psycopg.connect(settings.DATABASE_URL)
    inserted = skipped = malformed = 0

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = _pick(row, "title")
                description = _pick(row, "description")
                difficulty_raw = (_pick(row, "difficulty") or "").strip().lower()
                difficulty = DIFFICULTY_MAP.get(difficulty_raw)

                if not title or not description or not difficulty:
                    malformed += 1
                    continue

                slug = _pick(row, "title_slug") or _slugify(title)
                tags = _parse_tags(_pick(row, "topic_tags"))

                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM practice_problems WHERE title_slug = %s", (slug,))
                    if cur.fetchone():
                        skipped += 1
                        continue

                    cur.execute(
                        """
                        INSERT INTO practice_problems (title, title_slug, difficulty, description, topic_tags)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (title, slug, difficulty, description, json.dumps(tags)),
                    )
                    inserted += 1

                if inserted % 100 == 0 and inserted:
                    conn.commit()

        conn.commit()
    finally:
        conn.close()

    print(f"Imported {inserted} problems. Skipped {skipped} already present. {malformed} rows unusable.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_practice_problems.py path/to/leetcode.csv")
        sys.exit(1)
    import_csv(sys.argv[1])
