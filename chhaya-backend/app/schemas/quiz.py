"""Pydantic request and response schemas for the quiz API (Features 7 & 8)."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class QuizGenerateIn(BaseModel):
    """What the student sends to kick off quiz generation."""
    note_id: str
    num_questions: int = Field(ge=1, le=20)
    min_marks: int = Field(ge=1, le=10)
    max_marks: int = Field(ge=1, le=10)
    difficulty: str = Field(pattern="^(easy|medium|hard)$")

    @model_validator(mode="after")
    def check_marks_range(self):
        if self.max_marks < self.min_marks:
            raise ValueError("max_marks must be >= min_marks")
        return self


class QuizQuestionOut(BaseModel):
    id: str
    question_text: str
    marks: int
    difficulty: str


class QuizOut(BaseModel):
    """Summary of a quiz — shown on the list page. Includes grading fields (null until graded)."""
    id: str
    chapter_id: str
    note_id: str | None
    title: str
    difficulty: str
    num_questions: int
    min_marks: int
    max_marks: int
    duration_minutes: int
    attempt_number: int
    status: str
    ends_at: datetime | None
    submitted_at: datetime | None
    created_at: datetime | None
    # Feature 8 grading fields — null until graded
    total_score: int | None
    max_score: int | None
    percentage: float | None
    pass_status: str | None
    graded_at: datetime | None


class QuizDetailOut(BaseModel):
    """Full quiz — shown on the session page (includes questions)."""
    id: str
    chapter_id: str
    note_id: str | None
    title: str
    difficulty: str
    num_questions: int
    min_marks: int
    max_marks: int
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


# ── Feature 8 schemas ─────────────────────────────────────────────────────────

class GradedAnswerOut(BaseModel):
    """One question's grading result — shown in the results breakdown."""
    question_id: str
    question_text: str
    answer_text: str
    marks_obtained: int
    max_marks: int
    feedback: str


class QuizResultOut(BaseModel):
    """Full graded result for one quiz attempt."""
    id: str
    chapter_id: str
    title: str
    difficulty: str
    attempt_number: int
    num_questions: int
    total_score: int
    max_score: int
    percentage: float
    pass_status: str
    graded_at: datetime
    graded_answers: list[GradedAnswerOut]
