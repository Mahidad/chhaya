"""
`TeacherProfile` = the structured "teaching style fingerprint" Gemini
extracts from a reference source's transcripts.

This is the single most important table in Chhaya: nearly every other
feature (study guides, uncovered-topic explanations, voice narration
pacing, the tutor chat) reads a TeacherProfile and asks the AI to write
"in this style". Get this table right and Group 2, 3, and 4's features
all have something solid to build against.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    source_id = Column(
        String, ForeignKey("reference_sources.id"), nullable=False, unique=True
    )

    display_name = Column(String, nullable=False)  # e.g. "Rahman Sir - DSA style"
    is_favorite = Column(Boolean, default=False)

    # Human-readable summary fields (shown directly on the profile card in the UI)
    pacing = Column(String, nullable=True)              # "slow" | "moderate" | "fast"
    vocabulary_level = Column(String, nullable=True)     # "beginner" | "intermediate" | "advanced"
    analogy_frequency = Column(String, nullable=True)    # "low" | "medium" | "high"
    example_density = Column(String, nullable=True)      # "low" | "medium" | "high"

    # The full structured JSON Gemini returned, kept as-is so future
    # features (e.g. voice narration pacing) can read fields we didn't
    # anticipate needing a dedicated column for yet.
    raw_style_profile = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    source = relationship("ReferenceSource", back_populates="teacher_profile")
