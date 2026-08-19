"""
Orchestration for Module 3's Concept Map active-recall game (Lamia).
No AI call, no pending/generating status -- extraction
(app/utils/concept_extraction.py) is local and fast enough to run inside
the same request, so a map is always created already 'ready' or 'failed'.
"""

import psycopg

from app.models.concept_map import ConceptMap, ConceptMapAttempt, ConceptMapStatus, ExtractionMode
from app.repositories.concept_map_repository import concept_map_repository, concept_map_attempt_repository
from app.repositories.study_guide_repository import study_guide_repository
from app.services.course_service import get_chapter_for_user
from app.utils.concept_extraction import extract_text_blanks, extract_formula_blanks
from app.utils.exceptions import NotFoundError


def create_and_generate(
    db: psycopg.Connection, *, user_id: str, title: str, extraction_mode: str,
    chapter_id: str | None, source_study_guide_id: str | None, raw_text: str | None,
) -> ConceptMap:
    if extraction_mode not in (ExtractionMode.TEXT, ExtractionMode.FORMULA):
        raise ValueError(f"Unknown extraction_mode: {extraction_mode}")

    if bool(source_study_guide_id) == bool(raw_text and raw_text.strip()):
        raise ValueError("Provide either a study guide to generate from, or pasted text -- not both, not neither.")

    if chapter_id:
        get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)

    source_content_type = None
    source_content_id = None

    if source_study_guide_id:
        guide = study_guide_repository.get(db, source_study_guide_id)
        if not guide or guide.user_id != user_id:
            raise NotFoundError("That study guide was not found.")
        if not guide.content:
            raise ValueError("That study guide doesn't have any generated content yet.")
        text = guide.content
        source_content_type = "study_guide"
        source_content_id = guide.id
    else:
        text = raw_text

    try:
        if extraction_mode == ExtractionMode.TEXT:
            items, is_basic_mode = extract_text_blanks(text)
        else:
            items, is_basic_mode = extract_formula_blanks(text)

        if not items:
            raise ValueError(
                "Couldn't find enough concepts to build a game from that text -- "
                "try a longer passage, or switch modes if this is mostly formulas/prose."
            )

        return concept_map_repository.create(
            db,
            obj_in={
                "user_id": user_id,
                "chapter_id": chapter_id,
                "title": title,
                "extraction_mode": extraction_mode,
                "source_content_type": source_content_type,
                "source_content_id": source_content_id,
                "items": items,
                "is_basic_mode": is_basic_mode,
                "status": ConceptMapStatus.READY,
            },
        )
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        return concept_map_repository.create(
            db,
            obj_in={
                "user_id": user_id,
                "chapter_id": chapter_id,
                "title": title,
                "extraction_mode": extraction_mode,
                "source_content_type": source_content_type,
                "source_content_id": source_content_id,
                "items": [],
                "is_basic_mode": False,
                "status": ConceptMapStatus.FAILED,
                "error_message": str(exc),
            },
        )


def list_maps_for_user(db: psycopg.Connection, *, user_id: str) -> list[ConceptMap]:
    return concept_map_repository.list_for_user(db, user_id=user_id)


def list_maps_for_chapter(db: psycopg.Connection, *, user_id: str, chapter_id: str) -> list[ConceptMap]:
    get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)
    return concept_map_repository.list_for_chapter(db, chapter_id=chapter_id, user_id=user_id)


def get_map_for_user(db: psycopg.Connection, *, user_id: str, map_id: str) -> ConceptMap:
    concept_map = concept_map_repository.get_for_user(db, map_id=map_id, user_id=user_id)
    if not concept_map:
        raise NotFoundError("Concept map not found.")
    return concept_map


def delete_map(db: psycopg.Connection, *, user_id: str, map_id: str) -> None:
    concept_map = get_map_for_user(db, user_id=user_id, map_id=map_id)
    concept_map_repository.delete(db, id=concept_map.id)


def record_attempt(
    db: psycopg.Connection, *, user_id: str, map_id: str, correct_count: int, total_count: int
) -> ConceptMapAttempt:
    # Ownership check -- can't log an attempt against a map you don't own.
    get_map_for_user(db, user_id=user_id, map_id=map_id)
    return concept_map_attempt_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "concept_map_id": map_id,
            "correct_count": correct_count,
            "total_count": total_count,
        },
    )


def list_attempts_for_map(db: psycopg.Connection, *, user_id: str, map_id: str) -> list[ConceptMapAttempt]:
    get_map_for_user(db, user_id=user_id, map_id=map_id)
    return concept_map_attempt_repository.list_for_map(db, concept_map_id=map_id, user_id=user_id)
