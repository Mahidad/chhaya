"""Pydantic request and response schemas for the quiz API (Feature 7)."""

from datetime import datetime

from pydantic import BaseModel, Field


class QuizGenerateIn(BaseModel):
    """What the student sends to kick off quiz generation."""
    chapter_id: str
    num_questions: int = Field(ge=1, le=20)
    marks_per_question: int = Field(ge=1, le=10)
    difficulty: str = Field(pattern="^(easy|medium|hard)$")


class QuizQuestionOut(BaseModel):
    id: str
    question_text: str
    marks: int
    difficulty: str


class QuizOut(BaseModel):
    """Summary of a quiz — shown on the list page."""
    id: str
    chapter_id: str
    title: str
    difficulty: str
    num_questions: int
    marks_per_question: int
    duration_minutes: int
    attempt_number: int
    status: str
    ends_at: datetime | None
    submitted_at: datetime | None
    created_at: datetime | None


class QuizDetailOut(BaseModel):
    """Full quiz — shown on the session page (includes questions)."""
    id: str
    chapter_id: str
    title: str
    difficulty: str
    num_questions: int
    marks_per_question: int
    duration_minutes: int
    attempt_number: int
    status: str
    ends_at: datetime | None
    submitted_at: datetime | None
    created_at: datetime | None
    questions: list[QuizQuestionOut]


class QuizStartOut(BaseModel):
    """Returned when a student starts the quiz — frontend uses ends_at for timer."""
    id: str
    status: str
    started_at: datetime
    ends_at: datetime


class AnswerIn(BaseModel):
    """One student answer linked to a question."""
    question_id: str
    answer_text: str


class QuizSubmitIn(BaseModel):
    """List of answers the student submits."""
    answers: list[AnswerIn]


class QuizSubmitOut(BaseModel):
    """What the backend returns after accepting a submission."""
    id: str
    status: str
    submitted_at: datetime
