"""
Orchestration for Module 2's Word Lookup & Personal Glossary (Lamia).
`lookup_word` is a pure pass-through to the local dictionary util (no
database involved -- nothing is saved until the student explicitly chooses
to). Everything below it is plain CRUD against glossary_entries, scoped to
a chapter the student owns, same shape as every other Module 2 service.
"""

import psycopg

from app.models.glossary import GlossaryEntry
from app.repositories.glossary_repository import glossary_repository
from app.services.course_service import get_chapter_for_user
from app.utils.dictionary import lookup_word as _lookup_word
from app.utils.exceptions import NotFoundError


def lookup_word(word: str, topic: str | None = None) -> dict:
    return _lookup_word(word, topic=topic)


def save_glossary_entry(
    db: psycopg.Connection, *, user_id: str, chapter_id: str, term: str,
    definition: str, part_of_speech: str | None, source: str,
) -> GlossaryEntry:
    get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)
    return glossary_repository.create(
        db,
        obj_in={
            "user_id": user_id, "chapter_id": chapter_id, "term": term,
            "definition": definition, "part_of_speech": part_of_speech, "source": source,
        },
    )


def list_glossary_for_chapter(db: psycopg.Connection, *, user_id: str, chapter_id: str) -> list[GlossaryEntry]:
    get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)
    return glossary_repository.list_for_chapter(db, chapter_id=chapter_id, user_id=user_id)


def get_entry_for_user(db: psycopg.Connection, *, user_id: str, entry_id: str) -> GlossaryEntry:
    entry = glossary_repository.get_for_user(db, entry_id=entry_id, user_id=user_id)
    if not entry:
        raise NotFoundError("Glossary entry not found.")
    return entry


def update_glossary_entry(db: psycopg.Connection, *, user_id: str, entry_id: str, definition: str) -> GlossaryEntry:
    entry = get_entry_for_user(db, user_id=user_id, entry_id=entry_id)
    return glossary_repository.update(db, db_obj=entry, obj_in={"definition": definition, "source": "custom"})


def delete_glossary_entry(db: psycopg.Connection, *, user_id: str, entry_id: str) -> None:
    entry = get_entry_for_user(db, user_id=user_id, entry_id=entry_id)
    glossary_repository.delete(db, id=entry.id)
