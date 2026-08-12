"""
Orchestration for coding style profiles: create (runs the crude analyzer
from app/utils/code_style_analyzer.py -- no AI, no waiting, unlike every
other "create_and_process" service in this app), list, rename/favorite,
delete. Mirrors teacher_profile_service.py's shape closely on purpose --
same feature family (a library of style profiles a student built up),
different kind of style underneath.
"""

import psycopg

from app.repositories.code_style_profile_repository import code_style_profile_repository
from app.schemas.code_style_profile import CodeStyleProfileCreate, CodeStyleProfileUpdate
from app.utils.code_style_analyzer import analyze_code_style
from app.utils.exceptions import NotFoundError


def create_profile(db: psycopg.Connection, *, user_id: str, payload: CodeStyleProfileCreate):
    """
    Unlike ingesting a reference source, this never touches `status` --
    analyze_code_style runs synchronously and instantly (it's regex over
    a string already in memory, not a network call), so there's no
    pending/processing state worth modeling here.
    """
    extracted = analyze_code_style(payload.sample_code, payload.language)
    return code_style_profile_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "label": payload.label,
            "language": payload.language,
            "sample_code": payload.sample_code,
            **extracted,
        },
    )


def list_profiles_for_user(db: psycopg.Connection, *, user_id: str):
    return code_style_profile_repository.list_for_user(db, user_id=user_id)


def _get_owned_profile(db: psycopg.Connection, *, user_id: str, profile_id: str):
    profile = code_style_profile_repository.get(db, profile_id)
    if not profile or str(profile.user_id) != str(user_id):
        raise NotFoundError("Coding style profile not found.")
    return profile


def update_profile(db: psycopg.Connection, *, user_id: str, profile_id: str, payload: CodeStyleProfileUpdate):
    profile = _get_owned_profile(db, user_id=user_id, profile_id=profile_id)
    changes = payload.model_dump(exclude_unset=True)
    return code_style_profile_repository.update(db, db_obj=profile, obj_in=changes)


def delete_profile(db: psycopg.Connection, *, user_id: str, profile_id: str) -> None:
    profile = _get_owned_profile(db, user_id=user_id, profile_id=profile_id)
    code_style_profile_repository.delete(db, id=profile.id)
