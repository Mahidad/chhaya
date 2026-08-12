from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NoteUpdate(BaseModel):
    """
    Used for both renaming (title) and editing a text note's body
    (text_content). Both fields are optional so the frontend can send
    just the one that changed -- None means "leave as-is", not "clear
    it", see note_service.update_note for how that's applied.
    """
    title: str | None = None
    text_content: str | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chapter_id: str
    title: str
    note_type: str
    text_content: str | None
    created_at: datetime
    updated_at: datetime
