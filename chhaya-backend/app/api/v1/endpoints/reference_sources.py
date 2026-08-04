import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.teacher_profile_repository import teacher_profile_repository
from app.schemas.reference_source import ReferenceSourceCreate, ReferenceSourceOut
from app.schemas.teacher_profile import TeacherProfileOut
from app.services import reference_source_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/reference-sources", tags=["reference-sources"])


@router.post("", response_model=ReferenceSourceOut, status_code=status.HTTP_201_CREATED)
def create_reference_source(
    payload: ReferenceSourceCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Runs ingestion synchronously for now (see the docstring in
    reference_source_service.create_and_process for why, and what to
    change when this needs to move to a background task).
    """
    return reference_source_service.create_and_process(
        db, user_id=current_user.id, payload=payload
    )


@router.get("", response_model=list[ReferenceSourceOut])
def list_reference_sources(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return reference_source_service.list_sources_for_user(db, user_id=current_user.id)


@router.get("/{source_id}", response_model=ReferenceSourceOut)
def get_reference_source(
    source_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The frontend's "analysing" screen polls this endpoint every couple
    of seconds and watches `status` go pending -> processing -> ready/failed."""
    try:
        return reference_source_service.get_source_for_user(
            db, user_id=current_user.id, source_id=source_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{source_id}/profile", response_model=TeacherProfileOut)
def get_source_profile(
    source_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Only meaningful once the source's `status` is "ready" -- the frontend
    calls this right after it sees that status flip, rather than polling
    it separately. 404s until the profile exists, which naturally covers
    both "still processing" and "processing failed".
    """
    # Confirms the source belongs to this user before leaking profile data.
    try:
        reference_source_service.get_source_for_user(
            db, user_id=current_user.id, source_id=source_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    profile = teacher_profile_repository.get_by_source(db, source_id=source_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No style profile yet for this source.",
        )
    return profile


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reference_source(
    source_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        reference_source_service.delete_source(
            db, user_id=current_user.id, source_id=source_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
