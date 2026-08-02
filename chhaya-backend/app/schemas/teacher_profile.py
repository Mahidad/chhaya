from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TeacherProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    display_name: str
    is_favorite: bool
    pacing: str | None
    vocabulary_level: str | None
    analogy_frequency: str | None
    example_density: str | None
    raw_style_profile: dict[str, Any] | None
    created_at: datetime


class TeacherProfileUpdate(BaseModel):
    """Used by the Style Library (Module 2, Mahidad F2) to rename / favorite
    a profile -- included now since the model already supports it."""
    display_name: str | None = None
    is_favorite: bool | None = None
