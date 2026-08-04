import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.teacher_profile import TeacherProfileOut, TeacherProfileUpdate
from app.services import teacher_profile_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/teacher-profiles", tags=["teacher-profiles"])


@router.get("", response_model=list[TeacherProfileOut])
def list_teacher_profiles(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Powers the Style Library screen -- one profile per successfully
    ingested reference source (see Feature 1)."""
    return teacher_profile_service.list_profiles_for_user(db, user_id=current_user.id)


@router.patch("/{profile_id}", response_model=TeacherProfileOut)
def update_teacher_profile(
    profile_id: str,
    payload: TeacherProfileUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    One endpoint handles both renaming AND favoriting/pinning, because
    they're the same operation from the API's point of view: "change some
    fields on this row."  The frontend just sends whichever field changed --
    `{"is_favorite": true}` for a pin click, `{"display_name": "..."}` for
    a rename. PATCH (partial update) is the right verb precisely because
    the caller isn't required to send every field, only what changed.
    """
    try:
        return teacher_profile_service.update_profile(
            db, user_id=current_user.id, profile_id=profile_id, payload=payload
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher_profile(
    profile_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        teacher_profile_service.delete_profile(
            db, user_id=current_user.id, profile_id=profile_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
