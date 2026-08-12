"""
Orchestration for Module 2's Import/Upload Personal Notes (Lamia). Text
notes are saved straight to the `text_content` column; image/pdf notes are
saved to disk through the exact same `_save_upload` shape as
exam_paper_service.py (UPLOAD_DIR + a random filename) -- it's the same
problem (accept an uploaded file, keep the original name off the URL,
remember where it landed) solved the same way.
"""

import os
import uuid
from datetime import datetime, timezone

import psycopg

from app.models.note import Note, NoteType
from app.repositories.note_repository import note_repository
from app.services.course_service import get_chapter_for_user
from app.utils.exceptions import NotFoundError

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "notes"
)


def _save_upload(file_bytes: bytes, original_filename: str) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(original_filename)[1] or ".bin"
    stored_name = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, stored_name)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


def create_note(
    db: psycopg.Connection,
    *,
    user_id: str,
    chapter_id: str,
    title: str,
    note_type: str,
    text_content: str | None = None,
    file_bytes: bytes | None = None,
    filename: str | None = None,
) -> Note:
    # The interconnection point with Course/Chapter: a note has to be
    # filed into a real chapter the student owns, same shape as the
    # teacher-profile ownership check in
    # study_guide_service.create_and_generate.
    get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)

    obj_in = {
        "user_id": user_id,
        "chapter_id": chapter_id,
        "title": title,
        "note_type": note_type,
    }

    if note_type == NoteType.TEXT:
        obj_in["text_content"] = text_content or ""
    else:
        if not file_bytes:
            raise ValueError("An image or PDF note requires an uploaded file.")
        obj_in["file_path"] = _save_upload(file_bytes, filename or "upload")

    return note_repository.create(db, obj_in=obj_in)


def list_notes_for_chapter(db: psycopg.Connection, *, user_id: str, chapter_id: str) -> list[Note]:
    get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)
    return note_repository.list_for_chapter(db, chapter_id=chapter_id, user_id=user_id)


def get_note_for_user(db: psycopg.Connection, *, user_id: str, note_id: str) -> Note:
    note = note_repository.get_for_user(db, note_id=note_id, user_id=user_id)
    if not note:
        raise NotFoundError("Note not found.")
    return note


def update_note(
    db: psycopg.Connection, *, user_id: str, note_id: str, title: str | None, text_content: str | None
) -> Note:
    note = get_note_for_user(db, user_id=user_id, note_id=note_id)
    updates: dict = {}
    if title is not None:
        updates["title"] = title
    if text_content is not None:
        if note.note_type != NoteType.TEXT:
            raise ValueError("Only text notes can have their content edited.")
        updates["text_content"] = text_content
    if not updates:
        return note
    updates["updated_at"] = datetime.now(timezone.utc)
    return note_repository.update(db, db_obj=note, obj_in=updates)


def delete_note(db: psycopg.Connection, *, user_id: str, note_id: str) -> None:
    note = get_note_for_user(db, user_id=user_id, note_id=note_id)
    if note.file_path and os.path.exists(note.file_path):
        try:
            os.remove(note.file_path)
        except OSError:
            pass
    note_repository.delete(db, id=note.id)
