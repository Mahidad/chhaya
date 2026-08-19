"""
VoiceNarration dataclass -- Module 3 Feature 1 (Lamia).

`audio_path` follows the same convention as Note.file_path and
ExamPaper.file_path: kept on the dataclass so the service can read and
delete the file on disk, excluded from VoiceNarrationOut so it never
reaches the frontend -- the audio is served through its own
`/voice-narrations/{id}/audio` endpoint instead.
"""

from dataclasses import dataclass
from datetime import datetime


class NarrationStatus:
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


@dataclass
class VoiceNarration:
    id: str
    user_id: str
    status: str
    created_at: datetime
    note_id: str | None = None
    study_guide_id: str | None = None
    teacher_profile_id: str | None = None
    voice_short_name: str | None = None
    rate: str | None = None
    error_message: str | None = None
    audio_path: str | None = None
    duration_seconds: int | None = None
