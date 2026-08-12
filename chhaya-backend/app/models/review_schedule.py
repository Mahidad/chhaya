"""Data model for Amiyo's Module 2 spaced-repetition review entries."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class ReviewSchedule:
    id: str
    user_id: str
    study_guide_id: str
    topic: str
    next_review_date: date
    interval_days: int = 0
    ease_factor: float = 2.5
    review_count: int = 0
    last_reviewed_on: date | None = None
    last_reminded_on: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
