"""
Narration dataclass -- Module 3's AI Voice Narration (Lamia).

A narration is a generated artifact attached to an existing piece of
content (a study guide or a personal note) -- it reuses the same
content_type/content_id polymorphic-reference pattern already established
in models/annotation.py (ContentType), rather than inventing a second,
parallel one.
"""

from dataclasses import dataclass
from datetime import datetime


class NarrationStatus:
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


@dataclass
class Narration:
    id: str
    user_id: str
    content_type: str
    content_id: str
    voice: str
    rate: str
    status: str
    created_at: datetime
    teacher_profile_id: str | None = None
    error_message: str | None = None
    narration_text: str | None = None
    audio_path: str | None = None
    is_mock: bool = False
