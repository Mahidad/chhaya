"""
API endpoints for Amiyo's Module 1 Feature 4 – Analytics Dashboard.

All routes are under the /progress prefix (kept for consistency with the
existing api.py router registration that teammates already see).

Endpoints
---------
  POST   /progress/study-sessions/start          Record a new session start
  PUT    /progress/study-sessions/{id}/end        Close a session + log duration
  POST   /progress/study-guide-views             Record a guide-view event
  GET    /progress/analytics/summary             Week-over-week totals + trends
  GET    /progress/analytics/chart-data          Per-day data for last 14 days
  POST   /progress/seed-sample-data              DEV ONLY – insert demo data

Frontend flow
-------------
  AnalyticsDashboardPage.jsx
    → GET /progress/analytics/summary    (summary cards + trend sentences)
    → GET /progress/analytics/chart-data (bar chart raw data)

  GuideDetailPage.jsx (one additive line)
    → POST /progress/study-guide-views   (fire-and-forget on guide open)
"""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsSummary,
    ChartDay,
    StudyGuideViewIn,
    StudyGuideViewOut,
    StudySessionEndIn,
    StudySessionOut,
)
from app.services import analytics_service

router = APIRouter(prefix="/progress", tags=["progress"])


# ── Study sessions ────────────────────────────────────────────────────────────

@router.post(
    "/study-sessions/start",
    response_model=StudySessionOut,
    status_code=status.HTTP_201_CREATED,
)
def start_study_session(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Called when a student begins a study session.
    Returns a session ID the frontend can use to close the session later.
    """
    return analytics_service.start_session(db, user_id=current_user.id)


@router.put(
    "/study-sessions/{session_id}/end",
    response_model=StudySessionOut,
)
def end_study_session(
    session_id: str,
    payload: StudySessionEndIn,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Called when a student finishes a session.
    Persists ended_at and duration_secs so study-time charts are accurate.
    """
    result = analytics_service.end_session(
        db,
        user_id=current_user.id,
        session_id=session_id,
        duration_secs=payload.duration_secs,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or does not belong to this user.",
        )
    return result


# ── Study guide views ─────────────────────────────────────────────────────────

@router.post(
    "/study-guide-views",
    response_model=StudyGuideViewOut,
    status_code=status.HTTP_201_CREATED,
)
def record_study_guide_view(
    payload: StudyGuideViewIn,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Called silently (fire-and-forget) by GuideDetailPage.jsx when a student
    opens a completed study guide. Powers the "guide views" chart and trends.
    """
    return analytics_service.record_guide_view(
        db, user_id=current_user.id, study_guide_id=payload.study_guide_id
    )


# ── Analytics read endpoints ──────────────────────────────────────────────────

@router.get("/analytics/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns this-week vs. last-week totals and human-readable trend sentences.
    Example response:
    {
      "this_week": {"sessions": 5, "guide_views": 3, "study_minutes": 120},
      "last_week": {"sessions": 4, "guide_views": 5, "study_minutes": 90},
      "trend_sessions": "You had 1 more sessions this week (+25%)",
      "trend_guides":   "You had 2 fewer study guides this week (−40%)",
      "trend_minutes":  "You had 30 more minutes studied this week (+33%)"
    }
    """
    return analytics_service.get_analytics_summary(db, user_id=current_user.id)


@router.get("/analytics/chart-data", response_model=list[ChartDay])
def get_chart_data(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns per-day session counts, guide views, and study minutes for the
    last 14 days. The frontend renders these as SVG bar charts.
    Example item: {"day": "2026-07-29", "session_count": 2, "guide_views": 1, "study_minutes": 45}
    """
    return analytics_service.get_chart_data(db, user_id=current_user.id)


# ── Dev / demo seed endpoint ──────────────────────────────────────────────────

@router.post("/seed-sample-data", tags=["dev"])
def seed_sample_data(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    DEV / DEMO ONLY — inserts 14 days of realistic sample data for the
    current user so the analytics dashboard has something to display.
    Safe to call multiple times (each call adds more data).
    Remove this endpoint before production deployment.
    """
    result = analytics_service.seed_sample_data(db, user_id=current_user.id)
    return {
        "message": "Sample data inserted.",
        "sessions_added": result["sessions_added"],
        "views_added": result["views_added"],
    }


@router.delete("/seed-sample-data", tags=["dev"])
def clear_analytics_data(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    DEV / DEMO ONLY — wipes ALL study_sessions and study_guide_views for
    the current user, so you can reset to real analytics after testing
    with seed data.
    """
    result = analytics_service.clear_analytics_data(db, user_id=current_user.id)
    return {
        "message": "All analytics data cleared.",
        "sessions_deleted": result["sessions_deleted"],
        "views_deleted": result["views_deleted"],
    }
