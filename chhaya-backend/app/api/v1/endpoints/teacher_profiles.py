import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.preference_profile import PreferenceProfileOut
from app.schemas.teacher_profile import TeacherProfileOut, TeacherProfileUpdate
from app.services import preference_service, teacher_profile_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/teacher-profiles", tags=["teacher-profiles"])


def _with_match_score(profile, match_score: float | None) -> TeacherProfileOut:
    return TeacherProfileOut(**profile.__dict__, match_score=match_score)


@router.get("", response_model=list[TeacherProfileOut])
def list_teacher_profiles(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Powers the Style Library screen -- one profile per successfully
    ingested reference source (see Feature 1). Each profile comes back
    with `match_score` attached: how closely it matches this student's
    computed preference profile, so the library can be sorted/badged by
    "closest to what you usually like" without a separate request per row.
    """
    pairs = teacher_profile_service.list_profiles_with_match_scores(db, user_id=current_user.id)
    return [_with_match_score(profile, score) for profile, score in pairs]


@router.get("/preference", response_model=PreferenceProfileOut)
def get_preference_profile(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    The student's computed "taste fingerprint" -- a weighted average
    across their whole Style Library (see preference_service.py for
    exactly how the weighting works). Recomputed automatically whenever a
    new profile is added or a favorite is toggled; this endpoint just
    reads whatever was last computed, it doesn't recompute on every call.

    404s if the library is empty -- there's nothing to have a preference
    about yet.
    """
    preference = preference_service.get_preference_profile(db, user_id=current_user.id)
    if preference is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No preference profile yet -- add at least one reference source first.",
        )
    return preference


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
