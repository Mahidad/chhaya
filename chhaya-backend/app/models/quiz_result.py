"""
QuizResult dataclass — replaces the SQLAlchemy ORM model.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class QuizResult:
    id: str
    user_id: str
    topic: str
    score_percent: float
    taken_at: datetime
    course: str | None = None
