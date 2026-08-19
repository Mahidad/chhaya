from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ConceptMapItem(BaseModel):
    id: str
    template: str
    answer: str


class ConceptMapCreate(BaseModel):
    title: str
    extraction_mode: str  # "text" | "formula"
    chapter_id: str | None = None
    # Exactly one of these two must be provided -- see
    # concept_map_service.create_and_generate for the validation.
    source_study_guide_id: str | None = None
    raw_text: str | None = None


class ConceptMapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    extraction_mode: str
    chapter_id: str | None
    items: list[ConceptMapItem]
    is_basic_mode: bool
    status: str
    error_message: str | None
    created_at: datetime


class ConceptMapAttemptCreate(BaseModel):
    correct_count: int
    total_count: int


class ConceptMapAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    concept_map_id: str
    correct_count: int
    total_count: int
    completed_at: datetime
