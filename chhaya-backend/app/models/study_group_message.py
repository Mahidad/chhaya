"""Database row model for a message posted inside a study group."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class StudyGroupMessage:
    id: str
    group_id: str
    user_id: str
    content: str
    is_pinned: bool
    created_at: datetime
