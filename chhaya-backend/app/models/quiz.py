"""Data models for Amiyo's Module 3 Feature 7 – Quiz Generation."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Quiz:
    id: str
    user_id: str
    chapter_id: str
    title: str
    difficulty: str
    num_questions: int
    min_marks: int
    max_marks: int
    duration_minutes: int
    attempt_number: int
    status: str
    answers: list | None = None
    started_at: datetime | None = None
    ends_at: datetime | None = None
    submitted_at: datetime | None = None
    created_at: datetime | None = None
    # Feature 8 grading fields
    total_score: int | None = None
    max_score: int | None = None
    percentage: float | None = None
    pass_status: str | None = None
    graded_answers: list | None = None
    graded_at: datetime | None = None


@dataclass
class QuizQuestion:
    id: str
    quiz_id: str
    question_text: str
    marks: int
    difficulty: str
