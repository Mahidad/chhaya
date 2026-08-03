"""
Feature (Omar, Module 1 item 3): upload and OCR past exam papers.

Standalone from Mahidad's tables today -- no foreign key into
reference_sources or teacher_profiles. It becomes load-bearing for
Module 2/3 later (predicting likely exam questions, matching quiz format),
but for Module 1 it's self-contained: upload a scan, get text back.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ExamPaperStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ExamPaper(Base):
    __tablename__ = "exam_papers"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=False)
    course = Column(String, nullable=True)
    file_path = Column(String, nullable=False)  # where the uploaded scan is stored on disk

    status = Column(String, nullable=False, default=ExamPaperStatus.PENDING)
    error_message = Column(String, nullable=True)
    extracted_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
