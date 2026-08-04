import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.study_guide import StudyGuideCreate, StudyGuideOut
from app.services import study_guide_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/study-guides", tags=["study-guides"])


@router.post("", response_model=StudyGuideOut, status_code=status.HTTP_201_CREATED)
def create_study_guide(
    payload: StudyGuideCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return study_guide_service.create_and_generate(
            db, user_id=current_user.id, payload=payload
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=list[StudyGuideOut])
def list_study_guides(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return study_guide_service.list_guides_for_user(db, user_id=current_user.id)


@router.get("/{guide_id}", response_model=StudyGuideOut)
def get_study_guide(
    guide_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return study_guide_service.get_guide_for_user(
            db, user_id=current_user.id, guide_id=guide_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
