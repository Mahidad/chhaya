"""
Course and Chapter dataclasses -- Module 2's organizational backbone
(Lamia). Two related dataclasses in one file, same pattern as
models/reference_source.py (ReferenceSource + Video): a Chapter always
belongs to exactly one Course, so it doesn't need its own file.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Course:
    id: str
    user_id: str
    title: str
    order_index: int
    created_at: datetime


@dataclass
class Chapter:
    id: str
    user_id: str
    course_id: str
    title: str
    order_index: int
    created_at: datetime
