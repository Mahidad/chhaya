from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PracticeProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    title_slug: str
    difficulty: str
    description: str
    topic_tags: list[Any] | None


class SuggestProblemsRequest(BaseModel):
    """Ask for problems similar to the work saved in a folder. difficulty
    is required -- the student picks easy/medium/hard before suggestions
    are generated, per the feature spec."""
    folder_id: str
    difficulty: str
    limit: int = 5


class StartAttemptRequest(BaseModel):
    problem_id: str
    folder_id: str | None = None


class SubmitAttemptRequest(BaseModel):
    submitted_code: str
    language: str


class PracticeAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    problem_id: str
    folder_id: str | None
    language: str | None
    submitted_code: str | None
    status: str
    is_correct: bool | None
    feedback: str | None
    time_complexity: str | None
    space_complexity: str | None
    seconds_taken: int | None
    started_at: datetime
    submitted_at: datetime | None


class DashboardOut(BaseModel):
    """Everything the Code Studio dashboard renders -- computed on request
    from practice_attempts, not stored. See practice_dashboard_service.py."""
    total_solved: int
    total_attempted: int
    accuracy_percent: float
    avg_seconds_to_solve: float | None
    by_difficulty: dict[str, int]
    growth: list[dict[str, Any]]        # cumulative solved per week
    activity: list[dict[str, Any]]      # minutes practiced per day this month
    rank_label: str
    rank_points: int
