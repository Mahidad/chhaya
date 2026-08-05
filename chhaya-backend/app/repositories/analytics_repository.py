"""
All raw SQL for Amiyo's Module 1 Feature 4 – Analytics Dashboard.

Design notes
------------
• Every query uses parameterized placeholders (%s) — no user input is ever
  interpolated into the SQL string.
• Aggregation is done in SQL (GROUP BY day) rather than Python loops so the
  DB does the heavy lifting and the result set stays small.
• The BaseRepository.create() helper is reused for simple INSERT operations
  (start session, record view). Custom read queries live here as plain methods.

What is recorded
----------------
1. study_sessions  – a row is inserted when a student starts a session
   (POST /progress/study-sessions/start) and updated with ended_at +
   duration_secs when they end it (PUT /progress/study-sessions/{id}/end).

2. study_guide_views – a row is inserted each time a student opens a
   completed guide's detail page (fired silently from GuideDetailPage.jsx).

Where it is recorded
--------------------
  Backend  : analytics_repository.py  (this file)
  Tables   : study_sessions, study_guide_views  (see sql/schema.sql)
  Service  : analytics_service.py orchestrates inserts + trend calculation
  Endpoints: app/api/v1/endpoints/progress.py
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import psycopg
from psycopg.rows import dict_row

from app.models.analytics import StudySession, StudyGuideView
from app.schemas.analytics import ChartDay, WeekTotals


# ── helpers ──────────────────────────────────────────────────────────────────

def _week_bounds(reference: date) -> tuple[datetime, datetime]:
    """
    Return (week_start, week_end) for the ISO week that contains `reference`.
    Week start = Monday 00:00 UTC, week end = Sunday 23:59:59.999 UTC.
    """
    monday = reference - timedelta(days=reference.weekday())
    week_start = datetime(monday.year, monday.month, monday.day, tzinfo=timezone.utc)
    week_end = week_start + timedelta(days=7) - timedelta(microseconds=1)
    return week_start, week_end


# ── Study Session queries ─────────────────────────────────────────────────────

def insert_study_session(db: psycopg.Connection, *, user_id: str) -> StudySession:
    """Insert a new open session row and return it."""
    session_id = str(uuid.uuid4())
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO study_sessions (id, user_id)
            VALUES (%s, %s)
            RETURNING *
            """,
            (session_id, user_id),
        )
        row = cur.fetchone()
    return StudySession(**row)


def close_study_session(
    db: psycopg.Connection,
    *,
    session_id: str,
    user_id: str,
    duration_secs: int,
) -> StudySession | None:
    """Set ended_at and duration_secs on an existing session. Returns None if not found."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            UPDATE study_sessions
               SET ended_at      = NOW(),
                   duration_secs = %s
             WHERE id = %s
               AND user_id = %s
            RETURNING *
            """,
            (duration_secs, session_id, user_id),
        )
        row = cur.fetchone()
    return StudySession(**row) if row else None


# ── Study Guide View queries ──────────────────────────────────────────────────

def insert_study_guide_view(
    db: psycopg.Connection, *, user_id: str, study_guide_id: str
) -> StudyGuideView:
    """Record one guide-view event."""
    view_id = str(uuid.uuid4())
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO study_guide_views (id, user_id, study_guide_id)
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (view_id, user_id, study_guide_id),
        )
        row = cur.fetchone()
    return StudyGuideView(**row)


# ── Aggregation queries ───────────────────────────────────────────────────────

def fetch_chart_data(
    db: psycopg.Connection, *, user_id: str, days: int = 14
) -> list[ChartDay]:
    """
    Return per-day session counts, guide views, and study minutes
    for the last `days` calendar days (today inclusive).

    How weekly trends are calculated
    ---------------------------------
    The frontend (and analytics_service.py) derives week totals by summing
    the ChartDay rows that fall within the current and previous ISO weeks.
    Calculation:
        this_week  = Mon 00:00 UTC … now
        last_week  = previous Mon 00:00 … previous Sun 23:59:59 UTC
        trend %    = (this - last) / last × 100
                     → "No data from last week" when last == 0
    """
    since = datetime.now(timezone.utc) - timedelta(days=days - 1)
    since_date = since.date()

    with db.cursor(row_factory=dict_row) as cur:
        # Sessions per day
        cur.execute(
            """
            SELECT DATE(started_at AT TIME ZONE 'UTC') AS day,
                   COUNT(*)                             AS session_count,
                   COALESCE(SUM(duration_secs), 0)      AS total_secs
              FROM study_sessions
             WHERE user_id   = %s
               AND started_at >= %s
             GROUP BY day
            """,
            (user_id, since_date),
        )
        session_rows = {r["day"]: r for r in cur.fetchall()}

        # Guide views per day
        cur.execute(
            """
            SELECT DATE(viewed_at AT TIME ZONE 'UTC') AS day,
                   COUNT(*)                           AS guide_views
              FROM study_guide_views
             WHERE user_id  = %s
               AND viewed_at >= %s
             GROUP BY day
            """,
            (user_id, since_date),
        )
        view_rows = {r["day"]: r for r in cur.fetchall()}

    # Build a complete list for every day in the window (missing days → zeros)
    chart = []
    for i in range(days):
        day = (since + timedelta(days=i)).date()
        s = session_rows.get(day, {})
        v = view_rows.get(day, {})
        chart.append(
            ChartDay(
                day=day,
                session_count=int(s.get("session_count", 0)),
                guide_views=int(v.get("guide_views", 0)),
                study_minutes=int(s.get("total_secs", 0)) // 60,
            )
        )
    return chart


def fetch_week_totals(
    db: psycopg.Connection, *, user_id: str, week_start: datetime, week_end: datetime
) -> WeekTotals:
    """Sum sessions, guide views, and study minutes within [week_start, week_end]."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT COUNT(*)                        AS sessions,
                   COALESCE(SUM(duration_secs), 0) AS total_secs
              FROM study_sessions
             WHERE user_id    = %s
               AND started_at BETWEEN %s AND %s
            """,
            (user_id, week_start, week_end),
        )
        sess = cur.fetchone()

        cur.execute(
            """
            SELECT COUNT(*) AS guide_views
              FROM study_guide_views
             WHERE user_id  = %s
               AND viewed_at BETWEEN %s AND %s
            """,
            (user_id, week_start, week_end),
        )
        views = cur.fetchone()

    return WeekTotals(
        sessions=int(sess["sessions"]),
        guide_views=int(views["guide_views"]),
        study_minutes=int(sess["total_secs"]) // 60,
    )


# ── Dev/demo seed data ────────────────────────────────────────────────────────

def insert_seed_data(db: psycopg.Connection, *, user_id: str) -> dict:
    """
    Insert realistic-looking sample data for the last 14 days so the
    analytics dashboard has something to display during development/demo.

    THIS IS FOR DEVELOPMENT ONLY. Call POST /progress/seed-sample-data.
    Safe to call multiple times (each call adds another round of data).
    """
    import random

    sessions_added = 0
    views_added = 0
    today = datetime.now(timezone.utc).date()

    with db.cursor() as cur:
        for offset in range(14):
            day = today - timedelta(days=offset)
            # Add 0–3 sessions on most days, fewer on weekends
            num_sessions = random.randint(0, 3) if day.weekday() < 5 else random.randint(0, 1)
            for _ in range(num_sessions):
                sid = str(uuid.uuid4())
                dur = random.randint(600, 5400)  # 10 min – 90 min
                started = datetime(day.year, day.month, day.day,
                                   random.randint(8, 21), tzinfo=timezone.utc)
                cur.execute(
                    """
                    INSERT INTO study_sessions (id, user_id, started_at, ended_at, duration_secs, is_seed)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    """,
                    (sid, user_id, started, started + timedelta(seconds=dur), dur),
                )
                sessions_added += 1

            # Add 0–2 guide views
            num_views = random.randint(0, 2)
            for _ in range(num_views):
                vid = str(uuid.uuid4())
                # Use a placeholder guide id (FK check skipped for seed data)
                cur.execute(
                    """
                    INSERT INTO study_guide_views (id, user_id, study_guide_id, viewed_at, is_seed)
                    VALUES (%s, %s, %s, %s, TRUE)
                    """,
                    (vid, user_id, "seed-placeholder",
                     datetime(day.year, day.month, day.day, tzinfo=timezone.utc)),
                )
                views_added += 1

    return {"sessions_added": sessions_added, "views_added": views_added}  # was missing!


def delete_all_analytics_data(db: psycopg.Connection, *, user_id: str) -> dict:
    """
    Delete ONLY seed rows (is_seed = TRUE) for this user.
    Real study sessions and guide views (is_seed = FALSE) are never touched.

    This is what the "Remove seed data" button on the dashboard calls.
    """
    with db.cursor() as cur:
        # Delete sessions flagged as seed
        cur.execute(
            "DELETE FROM study_sessions WHERE user_id = %s AND is_seed = TRUE",
            (user_id,),
        )
        sessions_deleted = cur.rowcount

        # Delete guide views flagged as seed OR that use the seed placeholder ID
        # (the second condition catches any rows inserted before the is_seed column existed)
        cur.execute(
            """
            DELETE FROM study_guide_views
             WHERE user_id = %s
               AND (is_seed = TRUE OR study_guide_id = 'seed-placeholder')
            """,
            (user_id,),
        )
        views_deleted = cur.rowcount

    return {"sessions_deleted": sessions_deleted, "views_deleted": views_deleted}
