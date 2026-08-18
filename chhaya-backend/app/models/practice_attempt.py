"""PracticeAttempt -- one row per problem a student starts."""

from dataclasses import dataclass
from datetime import datetime


class AttemptStatus:
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    ABANDONED = "abandoned"


@dataclass
class PracticeAttempt:
    id: str
    user_id: str
    problem_id: str
    status: str
    started_at: datetime
    folder_id: str | None = None
    language: str | None = None
    submitted_code: str | None = None
    is_correct: bool | None = None
    feedback: str | None = None
    time_complexity: str | None = None
    space_complexity: str | None = None
    seconds_taken: int | None = None
    submitted_at: datetime | None = None
