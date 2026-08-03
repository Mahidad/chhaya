"""
Feature (Lamia, Module 1 item 2): AI-generated study guides.

THE INTERCONNECTION WITH MAHIDAD'S WORK: `teacher_profile_id` below is a
foreign key straight into `teacher_profiles` -- the table Mahidad's
ingestion pipeline (Feature 1) and Style Library (Feature 3) already
populate and manage. A guide is meaningless without a style to write it
in, so this table cannot exist independently of that one. If Mahidad ever
renames or restructures TeacherProfile's columns, this is the file that
breaks -- worth a heads-up in the group chat before doing that.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class GuideStatus:
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class GuideDepth:
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class StudyGuide(Base):
    __tablename__ = "study_guides"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    teacher_profile_id = Column(String, ForeignKey("teacher_profiles.id"), nullable=False)

    topic = Column(String, nullable=False)
    depth = Column(String, nullable=False, default=GuideDepth.STANDARD)
    include_formula_sheet = Column(Boolean, default=False)
    include_bangla = Column(Boolean, default=False)

    status = Column(String, nullable=False, default=GuideStatus.PENDING)
    error_message = Column(String, nullable=True)

    content = Column(Text, nullable=True)
    formula_sheet_content = Column(Text, nullable=True)
    # Real translation isn't implemented yet (see study_guide_service.py) --
    # this column exists so the schema is ready the day it is.
    bangla_content = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
