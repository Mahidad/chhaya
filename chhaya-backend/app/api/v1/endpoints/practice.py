import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.practice import (
    DashboardOut,
    PracticeAttemptOut,
    PracticeProblemOut,
    StartAttemptRequest,
    SubmitAttemptRequest,
    SuggestProblemsRequest,
)
from app.services import practice_dashboard_service, practice_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/problems", response_model=list[PracticeProblemOut])
def list_problems(
    difficulty: str | None = None,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return practice_service.list_problems(db, difficulty=difficulty)


@router.post("/suggest")
def suggest_problems(
    payload: SuggestProblemsRequest,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reads the saved work in a folder and returns problems that exercise
    the same concepts, at the requested difficulty. Response is
    [{"problem": {...}, "reason": "..."}] -- the reason is why that
    problem was picked for this student, shown in the UI so the
    suggestion isn't a black box.
    """
    try:
        results = practice_service.suggest_problems(db, user_id=current_user.id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return [
        {"problem": PracticeProblemOut.model_validate(r["problem"]), "reason": r["reason"]}
        for r in results
    ]


@router.post("/attempts", response_model=PracticeAttemptOut, status_code=status.HTTP_201_CREATED)
def start_attempt(
    payload: StartAttemptRequest,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Starts the clock -- started_at is set server-side here, which is
    what makes the recorded solve time trustworthy."""
    try:
        return practice_service.start_attempt(db, user_id=current_user.id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/attempts/{attempt_id}/submit", response_model=PracticeAttemptOut)
def submit_attempt(
    attempt_id: str,
    payload: SubmitAttemptRequest,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return practice_service.submit_attempt(
            db, user_id=current_user.id, attempt_id=attempt_id, payload=payload
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/attempts", response_model=list[PracticeAttemptOut])
def list_attempts(
    db: psycopg.Connection = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return practice_service.list_attempts_for_user(db, user_id=current_user.id)


@router.get("/attempts/{attempt_id}", response_model=PracticeAttemptOut)
def get_attempt(
    attempt_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return practice_service.get_attempt_for_user(db, user_id=current_user.id, attempt_id=attempt_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(
    db: psycopg.Connection = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return practice_dashboard_service.get_dashboard(db, user_id=current_user.id)
