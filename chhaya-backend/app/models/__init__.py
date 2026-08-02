"""
Importing every model here means `from app.models import *` (used in
main.py to create tables, and by Alembic to autogenerate migrations)
registers all tables on Base.metadata -- even ones no other file happens
to import directly yet.
"""

from app.models.user import User
from app.models.reference_source import ReferenceSource, Video, SourceStatus, SourceType
from app.models.teacher_profile import TeacherProfile

__all__ = [
    "User",
    "ReferenceSource",
    "Video",
    "SourceStatus",
    "SourceType",
    "TeacherProfile",
]
