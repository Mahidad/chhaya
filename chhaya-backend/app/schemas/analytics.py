"""
Pydantic schemas for Amiyo's Module 1 Feature 4 – Analytics Dashboard.

Schemas cover:
  - Inputs  : starting/ending a session, recording a guide view
  - Outputs : per-day chart rows, summary totals, week-over-week trend strings
"""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


# ── Inputs ──────────────────────────────────────────────────────────────────

class StudySessionEndIn(BaseModel):
    """Body for PUT /progress/study-sessions/{id}/end"""
    duration_secs: int  # seconds spent in the session


class StudyGuideViewIn(BaseModel):
    """Body for POST /progress/study-guide-views"""
    study_guide_id: str


# ── Outputs ─────────────────────────────────────────────────────────────────

class StudySessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    started_at: datetime
    ended_at: datetime | None
    duration_secs: int | None


class StudyGuideViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_guide_id: str
    viewed_at: datetime


class ChartDay(BaseModel):
    """
    One data point on the charts — represents a single calendar day.
    The frontend renders these as SVG bars (no chart library needed).
    """
    day: date               # e.g. 2026-07-29
    session_count: int      # how many sessions were started that day
    guide_views: int        # how many study-guide views that day
    study_minutes: int      # total minutes studied (sum of duration_secs / 60)


class WeekTotals(BaseModel):
    """Aggregated totals for one ISO week (Mon–Sun)."""
    sessions: int
    guide_views: int
    study_minutes: int


class AnalyticsSummary(BaseModel):
    """
    Top-level payload returned by GET /progress/analytics/summary.

    `trend_sessions` and `trend_guides` are human-readable strings, e.g.:
      "You studied 3 more sessions than last week"
      "You viewed 20% fewer study guides than last week"
      "No data from last week to compare"
    """
    this_week: WeekTotals
    last_week: WeekTotals
    trend_sessions: str
    trend_guides: str
    trend_minutes: str
