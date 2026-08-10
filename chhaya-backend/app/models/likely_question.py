"""Data model for Gemini-generated likely exam-question practice sets."""

from dataclasses import dataclass
from datetime import datetime


class LikelyQuestionStatus:
    PENDING = "pending"
    ANALYZING = "analyzing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class LikelyQuestionSet:
    id: str
    user_id: str
    title: str
    status: str
    source_paper_count: int
    created_at: datetime
    course: str | None = None
    error_message: str | None = None
    source_paper_ids: dict | None = None
    analysis: dict | None = None
    predicted_questions: list | None = None
