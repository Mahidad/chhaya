from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TeacherProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    channel_name: str | None = None
    display_name: str
    is_favorite: bool
    is_saved: bool = False
    pacing: str | None
    vocabulary_level: str | None
    analogy_frequency: str | None
    example_density: str | None
    raw_style_profile: dict[str, Any] | None
    created_at: datetime
    # Module 3 (Lamia) -- see models/teacher_profile.py.
    narration_voice: str = "en-US-AriaNeural"
    narration_voice_is_guess: bool = True
    # Not a DB column -- computed fresh against the user's preference
    # profile at request time by preference_service.compute_match_score.
    # None when the user has no preference profile yet (empty library).
    match_score: float | None = None

class TeacherProfileUpdate(BaseModel):
    """Used by the Style Library (Module 2, Mahidad F2) to rename / favorite / save
    a profile -- included now since the model already supports it."""
    display_name: str | None = None
    is_favorite: bool | None = None
    is_saved: bool | None = None
    # Module 3 (Lamia): correcting Gemini's narration-voice guess. Setting
    # this always flips narration_voice_is_guess to False -- see
    # teacher_profile_service.update_profile.
    narration_voice: str | None = None

