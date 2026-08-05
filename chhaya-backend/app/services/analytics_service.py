"""
Orchestration for Amiyo's Module 1 Feature 4 – Analytics Dashboard.

This service sits between the API endpoints and the analytics_repository.
Its main job is:
  1. Delegate all DB reads/writes to analytics_repository (no SQL here).
  2. Compute week-over-week trend strings from WeekTotals data.

Why trends live here and not in the repository
-----------------------------------------------
The repository's job is data access; arithmetic and formatting belong in the
service layer. This also makes the trend logic easy to unit-test without a DB.

Trend calculation rules (also documented in analytics_repository.py)
--------------------------------------------------------------------
  this_week  = ISO week containing today (Monday 00:00 UTC → now)
  last_week  = previous ISO week (Monday 00:00 → Sunday 23:59:59 UTC)
  trend %    = (this - last) / last × 100, rounded to 0 decimal places
  edge cases:
    last == 0, this == 0  → "No activity yet"
    last == 0, this > 0   → "No data from last week to compare"
    change == 0           → "Same as last week"
"""

from datetime import date, datetime, timedelta, timezone

import psycopg

from app.repositories import analytics_repository
from app.schemas.analytics import (
    AnalyticsSummary,
    ChartDay,
    StudySessionOut,
    StudyGuideViewOut,
    WeekTotals,
)


# ── Session management ────────────────────────────────────────────────────────

def start_session(db: psycopg.Connection, *, user_id: str) -> StudySessionOut:
    session = analytics_repository.insert_study_session(db, user_id=user_id)
    return StudySessionOut(
        id=session.id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_secs=session.duration_secs,
    )


def end_session(
    db: psycopg.Connection,
    *,
    user_id: str,
    session_id: str,
    duration_secs: int,
) -> StudySessionOut | None:
    session = analytics_repository.close_study_session(
        db, session_id=session_id, user_id=user_id, duration_secs=duration_secs
    )
    if session is None:
        return None
    return StudySessionOut(
        id=session.id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_secs=session.duration_secs,
    )


# ── Guide view recording ──────────────────────────────────────────────────────

def record_guide_view(
    db: psycopg.Connection, *, user_id: str, study_guide_id: str
) -> StudyGuideViewOut:
    view = analytics_repository.insert_study_guide_view(
        db, user_id=user_id, study_guide_id=study_guide_id
    )
    return StudyGuideViewOut(
        id=view.id,
        study_guide_id=view.study_guide_id,
        viewed_at=view.viewed_at,
    )


# ── Chart data ────────────────────────────────────────────────────────────────

def get_chart_data(
    db: psycopg.Connection, *, user_id: str, days: int = 14
) -> list[ChartDay]:
    """Return per-day aggregates for the last `days` days (today inclusive)."""
    return analytics_repository.fetch_chart_data(db, user_id=user_id, days=days)


# ── Analytics summary + trends ────────────────────────────────────────────────

def get_analytics_summary(
    db: psycopg.Connection, *, user_id: str
) -> AnalyticsSummary:
    """
    Fetch this-week and last-week totals, then compute trend strings.
    """
    today = datetime.now(timezone.utc).date()

    this_start, this_end = analytics_repository._week_bounds(today)
    last_start, last_end = analytics_repository._week_bounds(
        today - timedelta(days=7)  # go back 7 days → always lands in previous ISO week
    )

    this_week = analytics_repository.fetch_week_totals(
        db, user_id=user_id, week_start=this_start, week_end=this_end
    )
    last_week = analytics_repository.fetch_week_totals(
        db, user_id=user_id, week_start=last_start, week_end=last_end
    )

    return AnalyticsSummary(
        this_week=this_week,
        last_week=last_week,
        trend_sessions=_build_trend(this_week.sessions, last_week.sessions, "sessions"),
        trend_guides=_build_trend(this_week.guide_views, last_week.guide_views, "study guides"),
        trend_minutes=_build_trend(this_week.study_minutes, last_week.study_minutes, "minutes studied"),
    )


# ── Seed (dev / demo only) ────────────────────────────────────────────────────

def seed_sample_data(db: psycopg.Connection, *, user_id: str) -> dict:
    """Insert 14 days of realistic-looking demo data. Dev/demo use only."""
    return analytics_repository.insert_seed_data(db, user_id=user_id)


def clear_analytics_data(db: psycopg.Connection, *, user_id: str) -> dict:
    """
    Wipe all study_sessions and study_guide_views for this user.
    Called by DELETE /progress/seed-sample-data.
    Use this to remove seeded demo data and return to real analytics.
    """
    return analytics_repository.delete_all_analytics_data(db, user_id=user_id)


# ── Private helpers ───────────────────────────────────────────────────────────

def _build_trend(this_val: int, last_val: int, unit: str) -> str:
    """
    Turn two integers into a human-readable week-over-week trend sentence.

    Examples:
      this=5, last=4 → "You had 1 more session this week (+25%)"
      this=3, last=5 → "You had 2 fewer sessions this week (−40%)"
      this=0, last=0 → "No activity yet"
      this=2, last=0 → "No data from last week to compare"
      this=4, last=4 → "Same as last week"
    """
    if this_val == 0 and last_val == 0:
        return "No activity yet"

    if last_val == 0:
        return "No data from last week to compare"

    diff = this_val - last_val
    pct = round((diff / last_val) * 100)

    if diff == 0:
        return f"Same as last week ({this_val} {unit})"

    direction = "more" if diff > 0 else "fewer"
    sign = "+" if diff > 0 else "−"
    abs_diff = abs(diff)
    abs_pct = abs(pct)

    return f"You had {abs_diff} {direction} {unit} this week ({sign}{abs_pct}%)"
