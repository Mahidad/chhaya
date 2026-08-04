import psycopg
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.quiz_result import QuizResultCreate, QuizResultOut, WeakTopic
from app.services import progress_service

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/quiz-results", response_model=QuizResultOut, status_code=201)
def record_quiz_result(
    payload: QuizResultCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Nothing in Module 1 calls this automatically yet -- see the docstring
    in progress_service.py. It's here so the dashboard below has real
    data to compute against while Module 3's quiz grading doesn't exist.
    """
    return progress_service.record_quiz_result(db, user_id=current_user.id, payload=payload)


@router.get("/weak-topics", response_model=list[WeakTopic])
def get_weak_topics(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return progress_service.get_weak_topics(db, user_id=current_user.id)
