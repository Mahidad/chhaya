"""
Orchestration for Module 3 Feature 2 (Lamia): the concept-map recall game.

Thin by design -- all the real work is in utils/concept_extractor.py,
which is deterministic (NLTK / ast / regex, no AI). This layer just picks
the right extractor, stores the result, and enforces ownership. Unlike
the AI-backed features there's no pending/generating status to poll:
extraction runs in milliseconds against text already in memory, so the
response comes back complete.
"""

import psycopg

from app.repositories.concept_map_repository import concept_map_repository
from app.schemas.concept_map import ConceptMapCreate
from app.utils import concept_extractor
from app.utils.exceptions import NotFoundError

VALID_SOURCE_KINDS = {"text", "code", "math"}


def create_concept_map(db: psycopg.Connection, *, user_id: str, payload: ConceptMapCreate):
    kind = (payload.source_kind or "text").lower()
    if kind not in VALID_SOURCE_KINDS:
        raise ValueError(f"source_kind must be one of {sorted(VALID_SOURCE_KINDS)}.")

    # extract_from_code raises ValueError on unparseable Python -- let it
    # propagate so the endpoint can tell the student their code didn't
    # parse, rather than silently saving an empty map.
    graph = concept_extractor.extract(payload.source_text, kind)

    if not graph["nodes"]:
        raise ValueError(
            "Couldn't find any concepts in that input -- try a longer passage, or check the source type."
        )

    return concept_map_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "title": payload.title,
            "source_kind": kind,
            "source_text": payload.source_text,
            "nodes": graph["nodes"],
            "edges": graph["edges"],
        },
    )


def list_concept_maps_for_user(db: psycopg.Connection, *, user_id: str):
    return concept_map_repository.list_for_user(db, user_id=user_id)


def get_concept_map_for_user(db: psycopg.Connection, *, user_id: str, concept_map_id: str):
    concept_map = concept_map_repository.get_for_user(
        db, concept_map_id=concept_map_id, user_id=user_id
    )
    if not concept_map:
        raise NotFoundError("Concept map not found.")
    return concept_map


def delete_concept_map(db: psycopg.Connection, *, user_id: str, concept_map_id: str) -> None:
    concept_map = get_concept_map_for_user(db, user_id=user_id, concept_map_id=concept_map_id)
    concept_map_repository.delete(db, id=concept_map.id)
