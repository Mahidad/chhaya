"""
StudyGuide dataclass — replaces the SQLAlchemy ORM model.

Status and depth are kept as plain string constants (same as before) so
no call site needs to change.
"""

from dataclasses import dataclass
from datetime import datetime


class GuideStatus:
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class GuideDepth:
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


@dataclass
class StudyGuide:
    id: str
    user_id: str
    teacher_profile_id: str
    topic: str
    depth: str
    status: str
    created_at: datetime
    include_formula_sheet: bool = False
    include_bangla: bool = False
    error_message: str | None = None
    content: str | None = None
    formula_sheet_content: str | None = None
    bangla_content: str | None = None
