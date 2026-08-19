from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NarrationCreate(BaseModel):
    content_type: str          # "study_guide" | "note"
    content_id: str
    # For a study guide this can be omitted -- the guide's own
    # teacher_profile_id is used automatically. For a note there's no
    # inherent style to fall back on, so the frontend must send one.
    # Voice is NOT chosen here -- it's a fixed property of the resolved
    # teacher profile (see models/teacher_profile.py's narration_voice).
    teacher_profile_id: str | None = None


class VoiceOption(BaseModel):
    id: str
    label: str


class NarrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content_type: str
    content_id: str
    teacher_profile_id: str | None
    voice: str
    rate: str
    status: str
    error_message: str | None
    narration_text: str | None
    is_mock: bool
    created_at: datetime
