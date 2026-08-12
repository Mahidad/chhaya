import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.code_style_profile import (
    CodeStyleProfileCreate,
    CodeStyleProfileOut,
    CodeStyleProfileUpdate,
)
from app.services import code_style_profile_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/code-style-profiles", tags=["code-style-profiles"])


@router.post("", response_model=CodeStyleProfileOut, status_code=status.HTTP_201_CREATED)
def create_code_style_profile(
    payload: CodeStyleProfileCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unlike every other "create" endpoint tied to Gemini, this one
    responds immediately -- app/utils/code_style_analyzer.py is plain
    regex over the pasted sample, not a network call. No pending/
    generating status to poll.
    """
    return code_style_profile_service.create_profile(db, user_id=current_user.id, payload=payload)


@router.get("", response_model=list[CodeStyleProfileOut])
def list_code_style_profiles(
    db: psycopg.Connection = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return code_style_profile_service.list_profiles_for_user(db, user_id=current_user.id)


@router.patch("/{profile_id}", response_model=CodeStyleProfileOut)
def update_code_style_profile(
    profile_id: str,
    payload: CodeStyleProfileUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return code_style_profile_service.update_profile(
            db, user_id=current_user.id, profile_id=profile_id, payload=payload
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_code_style_profile(
    profile_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        code_style_profile_service.delete_profile(db, user_id=current_user.id, profile_id=profile_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
