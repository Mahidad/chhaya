"""
Re-exports every model so `from app.models import User` etc. continue to
work in any file that uses that import style.
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
