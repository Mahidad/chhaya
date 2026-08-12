"""Pydantic request and response schemas for the review schedule API."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class ReviewRatingIn(BaseModel):
    """SM-2 quality rating: Again=0, Hard=2, Good=4, Easy=5."""

    quality: int = Field(ge=0, le=5)


class ReviewScheduleOut(BaseModel):
    id: str
    study_guide_id: str
    topic: str
    next_review_date: date
    interval_days: int
    ease_factor: float
    review_count: int
    last_reviewed_on: date | None
    created_at: datetime | None


class ReminderCheckOut(BaseModel):
    checked: int
    sent: int
    skipped: int
