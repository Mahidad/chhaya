"""
Populates the practice problem bank from a public LeetCode dataset.

WHY A ONE-TIME IMPORT AND NOT A LIVE FETCH: LeetCode's GraphQL API is
private and their Terms of Service prohibit scraping/redistributing problem
content, which is also their copyrighted material. Instead this imports from
a PUBLIC dataset (the ones published on Kaggle) that each developer pulls
themselves. Because the import is static there's no weekly sync job and no
response cache to keep coherent -- the data doesn't change under us.

WHY THIS LIVES IN app/services AND NOT IN THE SCRIPT: two callers need it --
scripts/import_practice_problems.py (explicit, one-time) and
maybe_import_in_background() at the bottom of this file, which the FastAPI
lifespan calls so a teammate doesn't have to run anything. Keeping one copy
means the slug rules and the placeholder-row filter can't drift between them.

WHY THE AUTOMATIC IMPORT IS SAFE TO RUN AT STARTUP, when schema creation
deliberately isn't (see the lifespan docstring in app/main.py): it only ever
INSERTs reference data into a table that already exists, it never runs DDL,
and every failure path is swallowed with a message. The app boots and serves
traffic whether or not it succeeds.

The one thing it CANNOT do for you is create a Kaggle account: kagglehub
authenticates as an individual, so each developer needs their own token from
kaggle.com -> Settings -> API -> Create New Token. Without one it logs how to
fix that and stays out of the way.

The CSV needs columns for title, slug, difficulty, and description. Column
names vary between datasets, so COLUMN_ALIASES below maps the common
variants -- add to it if your CSV uses different headers.

Re-running is safe: rows are matched on title_slug and skipped if already
present, so a partial import can be resumed by just running it again.
"""

import csv
import glob
import json
import os
import re
import threading
from datetime import datetime

import psycopg

from app.core.config import settings
from app.repositories.practice_problem_repository import practice_problem_repository

COLUMN_ALIASES = {
    "title": ["title", "name", "question_title"],
    "title_slug": ["title_slug", "slug", "titleSlug", "question_slug"],
    "difficulty": ["difficulty", "level"],
    "description": ["description", "content", "question_content", "problem_statement"],
    "topic_tags": ["topic_tags", "tags", "related_topics", "topics"],
}

# Shortest real problem statement in the Kaggle dataset is ~200 chars; the
# stub rows are all exactly "SQL Schema" (10). 50 sits safely between them.
PLACEHOLDER_DESC_LEN = 50

DIFFICULTY_MAP = {
    "1": "easy", "2": "medium", "3": "hard",
    "easy": "easy", "medium": "medium", "hard": "hard",
}


class ImportError_(RuntimeError):
    """Raised when a dataset can't be fetched or contains no usable CSV."""


def _pick(row: dict, field: str) -> str | None:
    for alias in COLUMN_ALIASES[field]:
        if alias in row and row[alias]:
            return row[alias]
    return None


def _slugify(title: str) -> str:
    """Best-effort reproduction of LeetCode's own slug format.

    Runs of non-alphanumerics collapse to a SINGLE dash -- without that,
    "Pow(x, n)" becomes "pow-x--n" and "Range Sum Query - Immutable"
    becomes "range-sum-query---immutable", neither of which matches the
    real leetcode.com/problems/<slug> URL. title_slug is also the key this
    importer dedupes on, so a malformed one means a re-import duplicates
    the row instead of skipping it.
    """
    slug = "".join(c if c.isalnum() else "-" for c in title.lower())
    return re.sub(r"-+", "-", slug).strip("-")


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    for sep in (",", ";", "|"):
        if sep in raw:
            return [t.strip().lower().replace(" ", "-") for t in raw.split(sep) if t.strip()]
    return [raw.strip().lower().replace(" ", "-")]


def fetch_from_kaggle(slug: str) -> str:
    """Download a Kaggle dataset and return the path to its CSV.

    kagglehub hands back a cache DIRECTORY, not a file, so we still have to
    find the CSV inside it. Datasets sometimes ship several (a train/test
    split, or a stray metadata file), so when there's more than one we take
    the largest -- that's the problem bank.

    Needs Kaggle API credentials: ~/.kaggle/kaggle.json, or KAGGLE_USERNAME
    and KAGGLE_KEY in the environment.
    """
    try:
        import kagglehub
    except ImportError as exc:  # pragma: no cover - depends on install state
        raise ImportError_(
            "kagglehub is not installed -- run `pip install -r requirements.txt`."
        ) from exc

    try:
        path = kagglehub.dataset_download(slug)
    except Exception as exc:
        raise ImportError_(
            f"could not download '{slug}' from Kaggle ({exc}). "
            "Check the slug, and that Kaggle credentials are set "
            "(~/.kaggle/kaggle.json, or KAGGLE_USERNAME + KAGGLE_KEY)."
        ) from exc

    csvs = sorted(
        glob.glob(os.path.join(path, "**", "*.csv"), recursive=True),
        key=os.path.getsize,
        reverse=True,
    )
    if not csvs:
        raise ImportError_(f"no CSV found in {path} (contains: {os.listdir(path)})")

    return csvs[0]


def import_csv(csv_path: str, *, on_progress=None) -> tuple[int, int, int]:
    """Import a LeetCode CSV into practice_problems.

    Opens its own connection rather than borrowing from the request pool:
    this runs either from a CLI script (no pool) or from a background
    startup thread, and a multi-thousand-row insert has no business holding
    one of the ten pooled connections that serve HTTP traffic.

    Returns (inserted, skipped, malformed).
    """
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

                # Database problems in some datasets carry a stub description
                # ("SQL Schema") instead of the real prompt -- the statement
                # lives in an image on leetcode.com and never made it into the
                # CSV. A problem with no problem statement is not practisable,
                # so drop it rather than import a blank card.
                if len(description.strip()) < PLACEHOLDER_DESC_LEN:
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
                    if on_progress:
                        on_progress(inserted)

        conn.commit()
    finally:
        conn.close()

    return inserted, skipped, malformed


def resolve_csv(*, csv_path: str | None = None, slug: str | None = None) -> str:
    """Work out which CSV to import from, downloading it if necessary.

    Precedence: an explicit CSV path, then an explicit slug, then
    PRACTICE_DATASET_SLUG from the environment.
    """
    if csv_path:
        return csv_path

    slug = slug or settings.PRACTICE_DATASET_SLUG
    if not slug:
        raise ImportError_(
            "no dataset configured: set PRACTICE_DATASET_SLUG in .env, "
            "pass --kaggle OWNER/DATASET, or give a path to a CSV."
        )
    return fetch_from_kaggle(slug)


# ---------------------------------------------------------------------------
# Automatic import on startup
#
# Called from the FastAPI lifespan (app/main.py) so that a fresh clone has a
# working Practice tab without anyone running a command. Everything below is
# policy about WHEN to import; everything above is HOW.
# ---------------------------------------------------------------------------

_LOG_PREFIX = "[practice-bank]"

# Postgres advisory lock id for "a practice import is running". Any integer
# works as long as nothing else in this app picks the same one.
_IMPORT_LOCK_ID = 8412771

# Set once a thread has been started in THIS process, so a dev-server reload
# that re-imports this module can't stack up parallel imports.
_started = threading.Event()


def _has_kaggle_credentials() -> bool:
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        return True
    return os.path.exists(os.path.expanduser("~/.kaggle/kaggle.json"))


def last_successful_run(conn) -> datetime | None:
    """When the bank was last refreshed successfully, or None if never."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT max(finished_at) FROM practice_import_runs WHERE ok IS TRUE"
        )
        row = cur.fetchone()
        return row[0] if row else None


def refresh_is_due(conn) -> bool:
    """True if the bank is empty, or the last refresh is older than the
    configured interval. Uses the DATABASE's clock, not the process's, so a
    cron container in one timezone and a web dyno in another agree."""
    if practice_problem_repository.count(conn) == 0:
        return True
    last = last_successful_run(conn)
    if last is None:
        return True
    with conn.cursor() as cur:
        cur.execute("SELECT now() - %s > make_interval(days => %s)",
                    (last, settings.PRACTICE_REFRESH_DAYS))
        return cur.fetchone()[0]


def refresh_bank(*, trigger: str, csv_path: str | None = None, slug: str | None = None) -> dict:
    """Download the dataset and import anything new, recording the attempt.

    THIS IS THE WEEKLY SYNC. It is safe to run repeatedly: import_csv matches
    on title_slug and skips rows already present, so a re-run only ever adds
    problems the upstream dataset has gained since last time. Nothing is
    updated or deleted -- a problem that disappears upstream stays here,
    because students may have attempts pointing at it.

    An advisory lock keeps two triggers (cron firing while the web service
    also decided it was due) from downloading and inserting at once. If the
    lock is taken, this returns immediately rather than queueing.
    """
    conn = psycopg.connect(settings.DATABASE_URL, connect_timeout=15)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_lock(%s)", (_IMPORT_LOCK_ID,))
            if not cur.fetchone()[0]:
                return {"status": "skipped", "reason": "another import is already running"}

        dataset = slug or settings.PRACTICE_DATASET_SLUG
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO practice_import_runs (dataset_slug, trigger) VALUES (%s, %s) RETURNING id",
                (dataset, trigger),
            )
            run_id = cur.fetchone()[0]
        conn.commit()

        try:
            path = resolve_csv(csv_path=csv_path, slug=slug)
            inserted, skipped, malformed = import_csv(path)
        except Exception as exc:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE practice_import_runs SET finished_at = NOW(), ok = FALSE,"
                    " error_message = %s WHERE id = %s",
                    (str(exc)[:2000], run_id),
                )
            conn.commit()
            raise

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE practice_import_runs SET finished_at = NOW(), ok = TRUE,"
                " inserted = %s, skipped = %s, malformed = %s WHERE id = %s",
                (inserted, skipped, malformed, run_id),
            )
        conn.commit()
        return {"status": "ok", "inserted": inserted, "skipped": skipped,
                "malformed": malformed, "dataset": dataset}
    finally:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s)", (_IMPORT_LOCK_ID,))
            conn.commit()
        finally:
            conn.close()


def _run_refresh(trigger: str) -> None:
    try:
        result = refresh_bank(trigger=trigger)
        if result["status"] == "skipped":
            print(f"{_LOG_PREFIX} {result['reason']}")
        else:
            print(
                f"{_LOG_PREFIX} refresh done -- {result['inserted']} new problem(s), "
                f"{result['skipped']} already present, {result['malformed']} unusable."
            )
    except ImportError_ as exc:
        print(f"{_LOG_PREFIX} refresh skipped: {exc}")
    except Exception as exc:  # never let a refresh take down the API
        print(f"{_LOG_PREFIX} refresh failed: {exc!r}")


def maybe_import_in_background() -> None:
    """Refresh the bank on startup if one is due. Never raises.

    WHEN THIS RUNS: PRACTICE_AUTO_IMPORT is on, Kaggle credentials exist, and
    either the bank is empty or the last successful refresh is older than
    PRACTICE_REFRESH_DAYS.

    This is the fallback trigger. The reliable one is the scheduled job in
    render.yaml, which runs weekly whether or not anyone hits the site. Both
    call refresh_bank(), both take the same advisory lock, and both are
    idempotent -- so running both is harmless, and running only one still
    keeps the bank current.

    The work happens on a daemon thread: the download plus the insert pass
    takes well over a minute, and blocking the lifespan would mean the API
    refuses connections for that whole time.
    """
    try:
        if not settings.PRACTICE_AUTO_IMPORT:
            return
        if _started.is_set():
            return

        with psycopg.connect(settings.DATABASE_URL, connect_timeout=10) as conn:
            if not refresh_is_due(conn):
                return

        if not _has_kaggle_credentials():
            print(f"{_LOG_PREFIX} a refresh is due but no Kaggle credentials were found.")
            print(
                f"{_LOG_PREFIX}   Fix: get a token at kaggle.com -> Settings -> API -> "
                "Create New Token, save it to ~/.kaggle/kaggle.json (or set "
                "KAGGLE_USERNAME + KAGGLE_KEY), then restart."
            )
            print(
                f"{_LOG_PREFIX}   Or import manually: "
                "python scripts/import_practice_problems.py"
            )
            return

        _started.set()
        print(
            f"{_LOG_PREFIX} refresh due -- importing {settings.PRACTICE_DATASET_SLUG} "
            "in the background. The API is usable now."
        )
        threading.Thread(
            target=_run_refresh, args=("startup",), name="practice-bank-refresh", daemon=True
        ).start()
    except Exception as exc:
        print(f"{_LOG_PREFIX} could not start: {exc!r}")
