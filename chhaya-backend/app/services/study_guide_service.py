"""
Orchestration for Lamia's Feature 1, following the exact same shape as
reference_source_service.create_and_process: create a row, do the work,
update status, handle failure. Same "runs synchronously for now" note
applies here too -- see that file's docstring for the reasoning.
"""

import psycopg

from app.models.study_guide import StudyGuide, GuideStatus
from app.repositories.study_guide_repository import study_guide_repository
from app.repositories.teacher_profile_repository import teacher_profile_repository
from app.schemas.study_guide import StudyGuideCreate
from app.services import preference_service
from app.services.guide_generation_service import generate_guide_text, generate_formula_sheet, generate_bangla_translation
from app.utils.exceptions import NotFoundError


def create_and_generate(
    db: psycopg.Connection, *, user_id: str, payload: StudyGuideCreate
) -> StudyGuide:
    # The interconnection point with Mahidad's Feature 3: this profile has
    # to exist and belong to this user, or there's no style to write in.
    profile = teacher_profile_repository.get(db, payload.teacher_profile_id)
    if not profile or profile.user_id != user_id:
        raise NotFoundError("That teacher style profile was not found in your library.")

    guide = study_guide_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "teacher_profile_id": profile.id,
            "topic": payload.topic,
            "depth": payload.depth,
            "include_formula_sheet": payload.include_formula_sheet,
            "include_bangla": payload.include_bangla,
            "status": GuideStatus.PENDING,
        },
    )

    try:
        guide = study_guide_repository.update(
            db, db_obj=guide, obj_in={"status": GuideStatus.GENERATING}
        )

        content = generate_guide_text(
            topic=payload.topic,
            depth=payload.depth,
            style=profile.raw_style_profile or {},
        )
        updates = {"content": content, "status": GuideStatus.READY}

        if payload.include_formula_sheet:
            updates["formula_sheet_content"] = generate_formula_sheet(topic=payload.topic)

        if payload.include_bangla:
            updates["bangla_content"] = generate_bangla_translation(text=content)

        guide = study_guide_repository.update(db, db_obj=guide, obj_in=updates)
        # Generating a guide from a profile is a *usage* signal -- one of
        # the two inputs Mahidad's preference-profile weighting depends on
        # (see preference_service.py). Recomputed here, not just when a
        # new source is added, so "most-used teacher profile" stays
        # accurate the moment it changes rather than waiting on an
        # unrelated trigger elsewhere in the app.
        preference_service.recompute_preference_profile(db, user_id=user_id)
    except Exception as exc:  # noqa: BLE001
        guide = study_guide_repository.update(
            db,
            db_obj=guide,
            obj_in={"status": GuideStatus.FAILED, "error_message": str(exc)},
        )

    return guide


def list_guides_for_user(
    db: psycopg.Connection, *, user_id: str
) -> list[StudyGuide]:
    return study_guide_repository.list_for_user(db, user_id=user_id)


def get_guide_for_user(
    db: psycopg.Connection, *, user_id: str, guide_id: str
) -> StudyGuide:
    guide = study_guide_repository.get_for_user(db, guide_id=guide_id, user_id=user_id)
    if not guide:
        raise NotFoundError("Study guide not found.")
    return guide


def delete_guide(db: psycopg.Connection, *, user_id: str, guide_id: str) -> None:
    guide = get_guide_for_user(db, user_id=user_id, guide_id=guide_id)
    study_guide_repository.delete(db, id=guide.id)


def update_guide(
    db: psycopg.Connection, *, user_id: str, guide_id: str,
    topic: str | None = None, chapter_id: str | None = None,
    content: str | None = None, formula_sheet_content: str | None = None,
) -> StudyGuide:
    """
    Update a study guide's topic, chapter_id, content, or formula_sheet_content.
    To *unfile* a guide (remove it from any chapter), send chapter_id="NONE".
    """
    guide = get_guide_for_user(db, user_id=user_id, guide_id=guide_id)
    updates: dict = {}
    if topic is not None:
        updates["topic"] = topic
    if chapter_id is not None:
        updates["chapter_id"] = None if chapter_id == "NONE" else chapter_id
    if content is not None:
        updates["content"] = content
    if formula_sheet_content is not None:
        updates["formula_sheet_content"] = formula_sheet_content
    if not updates:
        return guide
    return study_guide_repository.update(db, db_obj=guide, obj_in=updates)
