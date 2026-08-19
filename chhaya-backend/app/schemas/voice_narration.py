from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class VoiceNarrationCreate(BaseModel):
    """
    Exactly one of note_id / study_guide_id must be set.

    teacher_profile_id is only meaningful alongside note_id: a study guide
    was already generated in a teacher's style, so its narration inherits
    that same profile automatically rather than letting the student pick a
    different (contradictory) voice. The validator below enforces both
    rules here, so a bad request is rejected before it reaches the service.
    """
    note_id: str | None = None
    study_guide_id: str | None = None
    teacher_profile_id: str | None = None

    @model_validator(mode="after")
    def check_exactly_one_source(self):
        if bool(self.note_id) == bool(self.study_guide_id):
            raise ValueError("Provide exactly one of note_id or study_guide_id.")
        if self.study_guide_id and self.teacher_profile_id:
            raise ValueError(
                "A study guide is already written in a teacher's style -- "
                "its narration uses that same profile, so teacher_profile_id can't be set here."
            )
        return self


class VoiceNarrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    note_id: str | None
    study_guide_id: str | None
    teacher_profile_id: str | None
    voice_short_name: str | None
    rate: str | None
    status: str
    error_message: str | None
    duration_seconds: int | None
    created_at: datetime
    # audio_path is deliberately absent -- audio is served through
    # GET /voice-narrations/{id}/audio, same as notes serve their files.
