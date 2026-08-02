"""
`ReferenceSource` = one YouTube playlist / video / course link a student
adds (e.g. "Prof. Rahman's Data Structures playlist").

`Video` = one video that belongs to that source, holding its transcript.
A playlist source has many videos; a single-video source has exactly one.

Splitting these into two tables (instead of one big row with a transcript
column) is what lets a playlist ingest 40 videos in parallel and show
per-video progress on the "analysing" screen, and it's the same shape
Module 3 (past-exam OCR) and Module 2 (study guides) will reuse: a parent
"thing the student uploaded" + child "pieces we extracted from it".
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# Plain string constants rather than a DB-level enum: easier to add a new
# status later (e.g. "queued") without an Alembic migration to alter an
# enum type, which is notoriously painful in Postgres.
class SourceStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class SourceType:
    YOUTUBE_VIDEO = "youtube_video"
    YOUTUBE_PLAYLIST = "youtube_playlist"
    COURSE_LINK = "course_link"


class ReferenceSource(Base):
    __tablename__ = "reference_sources"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False, default=SourceType.YOUTUBE_PLAYLIST)
    url = Column(String, nullable=False)

    status = Column(String, nullable=False, default=SourceStatus.PENDING)
    error_message = Column(String, nullable=True)  # populated only if status == FAILED

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="reference_sources")
    videos = relationship(
        "Video", back_populates="source", cascade="all, delete-orphan"
    )
    # one-to-one: a source gets at most one style profile once processing succeeds
    teacher_profile = relationship(
        "TeacherProfile",
        back_populates="source",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=_uuid)
    source_id = Column(String, ForeignKey("reference_sources.id"), nullable=False, index=True)

    youtube_video_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    order_index = Column(Integer, default=0)
    duration_seconds = Column(Integer, nullable=True)

    transcript_text = Column(Text, nullable=True)
    transcript_status = Column(String, nullable=False, default=SourceStatus.PENDING)

    source = relationship("ReferenceSource", back_populates="videos")
