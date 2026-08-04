"""
ExamPaper dataclass — replaces the SQLAlchemy ORM model.

`file_path` is intentionally kept here (it's a server-side storage detail)
even though it is excluded from `ExamPaperOut` so it never reaches the
frontend.  The exam-papers endpoint uses it to serve the raw file and to
clean up on delete.
"""

from dataclasses import dataclass
from datetime import datetime


class ExamPaperStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class ExamPaper:
    id: str
    user_id: str
    title: str
    file_path: str
    status: str
    created_at: datetime
    course: str | None = None
    error_message: str | None = None
    extracted_text: str | None = None
