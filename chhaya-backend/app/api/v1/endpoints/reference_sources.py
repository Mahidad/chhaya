import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.teacher_profile_repository import teacher_profile_repository
from app.schemas.reference_source import ReferenceSourceCreate, ReferenceSourceOut, ReferenceSourceUpdate
from app.schemas.teacher_profile import TeacherProfileOut
from app.services import preference_service, reference_source_service
from app.utils.exceptions import NotFoundError, DuplicateSourceError

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

    If this link (or, for a single video, this exact video) was already
    extracted by this user and `payload.force` isn't set, this returns
    409 instead of creating anything -- see DuplicateSourceError.
    """
    try:
        return reference_source_service.create_and_process(
            db, user_id=current_user.id, payload=payload
        )
    except DuplicateSourceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "existing_source_id": exc.existing_source_id,
                "existing_title": exc.existing_title,
            },
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


@router.get("/{source_id}/profiles", response_model=list[TeacherProfileOut])
def get_source_profiles(
    source_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    PLURAL -- a playlist source can produce more than one profile, one
    per detected instructor (see reference_source_service.py). A single
    video source will always return a list of exactly one. Only
    meaningful once the source's `status` is "ready"; returns an empty
    list otherwise rather than 404ing.

    Each profile includes `match_score` against the student's preference
    profile -- this is the actual answer to "which of these candidate
    videos/playlists is closest to what I usually like": ingest a few
    candidates on the same topic, open each one's detail page, and
    compare the match scores instead of guessing from the title alone.

    Replaces the old singular GET /{source_id}/profile endpoint -- update
    any frontend caller still using the singular path.
    """
    try:
        reference_source_service.get_source_for_user(
            db, user_id=current_user.id, source_id=source_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    profiles = teacher_profile_repository.list_by_source(db, source_id=source_id)
    preference = preference_service.get_preference_profile(db, user_id=current_user.id)
    if preference is None:
        return [TeacherProfileOut(**p.__dict__, match_score=None) for p in profiles]
    return [
        TeacherProfileOut(**p.__dict__, match_score=preference_service.compute_match_score(preference, p))
        for p in profiles
    ]


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
        
@router.patch("/{source_id}", response_model=ReferenceSourceOut)
def rename_reference_source(
    source_id: str,
    payload: ReferenceSourceUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return reference_source_service.rename_source(
            db, user_id=current_user.id, source_id=source_id, title=payload.title
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))