from datetime import datetime
from pydantic import BaseModel, ConfigDict


class QuizResultCreate(BaseModel):
    topic: str
    course: str | None = None
    score_percent: float


class QuizResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic: str
    course: str | None
    score_percent: float
    taken_at: datetime


class WeakTopic(BaseModel):
    """Not tied to a DB row -- this is a computed aggregate, built fresh
    on every request in progress_service.py, not stored anywhere."""
    topic: str
    course: str | None
    average_score: float
    attempts: int
    is_weak: bool
