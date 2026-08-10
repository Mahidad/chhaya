"""Request and response contracts for likely-question generation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LikelyQuestionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    course: str | None = Field(default=None, max_length=80)
    exam_paper_ids: list[str] = Field(min_length=1)
    question_count: int = Field(default=8, ge=3, le=20)


class LikelyQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    course: str | None
    status: str
    error_message: str | None
    source_paper_count: int
    source_paper_ids: dict | None
    analysis: dict | None
    predicted_questions: list | None
    created_at: datetime
