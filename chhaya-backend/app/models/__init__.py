"""
Importing every model here means `from app.models import *` (used in
main.py to create tables, and by Alembic to autogenerate migrations)
registers all tables on Base.metadata -- even ones no other file happens
to import directly yet.
"""

from app.models.user import User
from app.models.reference_source import ReferenceSource, Video, SourceStatus, SourceType
from app.models.teacher_profile import TeacherProfile
from app.models.study_guide import StudyGuide, GuideStatus, GuideDepth
from app.models.exam_paper import ExamPaper, ExamPaperStatus
from app.models.quiz_result import QuizResult

__all__ = [
    "User",
    "ReferenceSource",
    "Video",
    "SourceStatus",
    "SourceType",
    "TeacherProfile",
]
