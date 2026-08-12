"""
Business logic for Feature 3 (Teacher Profile Library CRUD + Favorites).

Notice how short this is compared to reference_source_service.py. That's
not a mistake -- a service's job is to hold logic, and "list my profiles"
or "rename this profile" barely has any. When a service doesn't need to
do much, it shouldn't pretend to. The value of the layer is consistency
(every feature has one), not that every service is complicated.
"""

import psycopg

from app.models.teacher_profile import TeacherProfile
from app.repositories.teacher_profile_repository import teacher_profile_repository
from app.schemas.teacher_profile import TeacherProfileUpdate
from app.services import preference_service
from app.utils.exceptions import NotFoundError


def list_profiles_for_user(
    db: psycopg.Connection, *, user_id: str
) -> list[TeacherProfile]:
    return teacher_profile_repository.list_for_user(db, user_id=user_id)


def _get_owned_profile(
    db: psycopg.Connection, *, user_id: str, profile_id: str
) -> TeacherProfile:
    """Shared by update and delete: fetch a profile and make sure it's
    actually this user's before doing anything to it. Centralizing this
    check here (instead of copy-pasting it into both endpoints) means
    there's exactly one place that could get the ownership check wrong."""
    profile = teacher_profile_repository.get(db, profile_id)
    if not profile or profile.user_id != user_id:
        raise NotFoundError("Style profile not found.")
    return profile


def update_profile(
    db: psycopg.Connection,
    *,
    user_id: str,
    profile_id: str,
    payload: TeacherProfileUpdate,
) -> TeacherProfile:
    profile = _get_owned_profile(db, user_id=user_id, profile_id=profile_id)
    # exclude_unset=True: only the fields the client actually sent get
    # touched, so toggling `is_favorite` alone never blanks out `display_name`.
    changes = payload.model_dump(exclude_unset=True)
    updated = teacher_profile_repository.update(db, db_obj=profile, obj_in=changes)

    # Favoriting is one of the two signals the preference weighting
    # formula depends on (see preference_service.py's docstring) -- a
    # pin/unpin should be reflected the moment it happens, not wait for
    # the next source to be added.
    if "is_favorite" in changes:
        preference_service.recompute_preference_profile(db, user_id=user_id)

    return updated


def delete_profile(
    db: psycopg.Connection, *, user_id: str, profile_id: str
) -> None:
    profile = _get_owned_profile(db, user_id=user_id, profile_id=profile_id)
    teacher_profile_repository.delete(db, id=profile.id)
    preference_service.recompute_preference_profile(db, user_id=user_id)


def list_profiles_with_match_scores(
    db: psycopg.Connection, *, user_id: str
) -> list[tuple]:
    """
    Returns [(profile, match_score_or_None), ...] -- match_score is None
    if this user has no preference profile yet (empty library, or a
    library that hasn't triggered a recompute yet). This is the function
    both the Style Library list and a reference source's /profiles
    endpoint call so a profile's match score means the same thing
    everywhere it's shown.
    """
    profiles = teacher_profile_repository.list_for_user(db, user_id=user_id)
    preference = preference_service.get_preference_profile(db, user_id=user_id)
    if preference is None:
        return [(p, None) for p in profiles]
    return [(p, preference_service.compute_match_score(preference, p)) for p in profiles]
