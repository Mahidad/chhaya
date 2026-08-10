import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.likely_question import LikelyQuestionCreate, LikelyQuestionOut
from app.services import likely_question_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/likely-questions", tags=["likely-questions"])


@router.post("", response_model=LikelyQuestionOut, status_code=status.HTTP_201_CREATED)
def create_likely_questions(
    payload: LikelyQuestionCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return likely_question_service.create_and_generate(db, user_id=current_user.id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("", response_model=list[LikelyQuestionOut])
def list_likely_question_sets(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return likely_question_service.list_sets_for_user(db, user_id=current_user.id)


@router.get("/{set_id}", response_model=LikelyQuestionOut)
def get_likely_question_set(
    set_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return likely_question_service.get_set_for_user(db, user_id=current_user.id, set_id=set_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_likely_question_set(
    set_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        likely_question_service.delete_set_for_user(db, user_id=current_user.id, set_id=set_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
