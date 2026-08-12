from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HighlightCreate(BaseModel):
    chapter_id: str | None = None
    content_type: str  # "study_guide" | "note"
    content_id: str
    quoted_text: str
    color: str = "amber"


class HighlightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chapter_id: str | None = None
    content_type: str
    content_id: str
    quoted_text: str
    color: str
    created_at: datetime
