"""
Highlight dataclass -- Module 2's Highlights feature (Lamia). (Sticky
notes were removed from this feature -- see git history / the zip from
2026-08-12 if that's ever wanted back.)

content_type / content_id together are a lightweight "polymorphic
reference" -- content_type is either "study_guide" or "note", and
content_id is the id of the matching row in that table. There's no
database foreign key for this on purpose (raw SQL has no way to FK a
single column at two different tables at once); annotation_service.py
checks ownership by looking the row up in the right repository before
ever creating a highlight against it.
"""

from dataclasses import dataclass
from datetime import datetime


class ContentType:
    STUDY_GUIDE = "study_guide"
    NOTE = "note"


@dataclass
class Highlight:
    id: str
    user_id: str
    chapter_id: str
    content_type: str
    content_id: str
    quoted_text: str
    color: str
    created_at: datetime
