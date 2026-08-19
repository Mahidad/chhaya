"""
Intentionally empty.

This used to re-export models so `from app.models import User` would work.
Nothing in the codebase imports that way -- every module imports from the
concrete file (`from app.models.user import User`) -- and the shim had
drifted to cover only 8 of the 19 model modules, so following it for one of
the other 11 gave you an ImportError instead of the convenience it promised.

If you want the short import style back, re-export ALL of them, and add new
models here as they're created.
"""

from app.models.user import User
from app.models.reference_source import ReferenceSource, Video, SourceStatus, SourceType
from app.models.teacher_profile import TeacherProfile
from app.models.study_guide import StudyGuide, GuideStatus, GuideDepth
from app.models.exam_paper import ExamPaper, ExamPaperStatus
from app.models.analytics import StudySession, StudyGuideView
from app.models.likely_question import LikelyQuestionSet, LikelyQuestionStatus
from app.models.review_schedule import ReviewSchedule
from app.models.quiz import Quiz, QuizQuestion
from app.models.study_group import StudyGroup, GroupInvitation, JoinRequest
from app.models.study_group_message import StudyGroupMessage

__all__ = [
    "User",
    "ReferenceSource",
    "Video",
    "SourceStatus",
    "SourceType",
    "TeacherProfile",
    "StudyGuide",
    "GuideStatus",
    "GuideDepth",
    "ExamPaper",
    "ExamPaperStatus",
    "StudySession",
    "StudyGuideView",
    "LikelyQuestionSet",
    "LikelyQuestionStatus",
    "ReviewSchedule",
    "Quiz",
    "QuizQuestion",
    "StudyGroup",
    "GroupInvitation",
    "JoinRequest",
    "StudyGroupMessage",
]

