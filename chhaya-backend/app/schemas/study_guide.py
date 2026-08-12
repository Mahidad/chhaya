from datetime import datetime
from pydantic import BaseModel, ConfigDict


class StudyGuideCreate(BaseModel):
    topic: str
    teacher_profile_id: str  # picked from GET /teacher-profiles -- see Style Library
    depth: str = "standard"  # "quick" | "standard" | "deep"
    include_formula_sheet: bool = False
    include_bangla: bool = False
    chapter_id: str | None = None


class StudyGuideUpdate(BaseModel):
    topic: str | None = None
    chapter_id: str | None = None
    content: str | None = None
    formula_sheet_content: str | None = None


class StudyGuideOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    teacher_profile_id: str
    topic: str
    depth: str
    include_formula_sheet: bool
    include_bangla: bool
    status: str
    error_message: str | None
    content: str | None
    formula_sheet_content: str | None
    bangla_content: str | None
    chapter_id: str | None = None
    created_at: datetime
