"""
Orchestration for Module 2's Highlights (Lamia). Every create call here
re-validates two ownership layers before writing anything: (1) the
chapter belongs to this user (via course_service), and (2) the content
item being highlighted (a study guide or a note) belongs to this user too
-- otherwise a student could highlight someone else's content just by
guessing its id, since content_id has no real foreign key (see the
comment in models/annotation.py for why).
"""

import psycopg

from app.models.annotation import Highlight, ContentType
from app.repositories.annotation_repository import highlight_repository
from app.repositories.study_guide_repository import study_guide_repository
from app.repositories.note_repository import note_repository
from app.services.course_service import get_chapter_for_user
from app.utils.exceptions import NotFoundError


def _assert_owns_content(db: psycopg.Connection, *, user_id: str, content_type: str, content_id: str) -> None:
    base_id = content_id.split("_")[-1].replace("-formula", "")
    if content_type == ContentType.STUDY_GUIDE:
        item = study_guide_repository.get(db, base_id)
    elif content_type == ContentType.NOTE:
        item = note_repository.get(db, base_id)
    else:
        raise ValueError(f"Unknown content_type: {content_type}")

    if not item or item.user_id != user_id:
        raise NotFoundError("The content you're trying to annotate was not found.")


# --------------------------------------------------------------------------
# Highlights
# --------------------------------------------------------------------------

def create_highlight(
    db: psycopg.Connection, *, user_id: str, chapter_id: str | None, content_type: str,
    content_id: str, quoted_text: str, color: str,
) -> Highlight:
    if chapter_id and chapter_id != "unfiled":
        try:
            get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)
        except Exception:
            chapter_id = None
    else:
        chapter_id = None

    _assert_owns_content(db, user_id=user_id, content_type=content_type, content_id=content_id)
    return highlight_repository.create(
        db,
        obj_in={
            "user_id": user_id, "chapter_id": chapter_id, "content_type": content_type,
            "content_id": content_id, "quoted_text": quoted_text, "color": color,
        },
    )


def list_highlights_for_content(
    db: psycopg.Connection, *, user_id: str, content_type: str, content_id: str
) -> list[Highlight]:
    return highlight_repository.list_for_content(
        db, content_type=content_type, content_id=content_id, user_id=user_id
    )


def delete_highlight(db: psycopg.Connection, *, user_id: str, highlight_id: str) -> None:
    highlight = highlight_repository.get_for_user(db, highlight_id=highlight_id, user_id=user_id)
    if not highlight:
        raise NotFoundError("Highlight not found.")
    highlight_repository.delete(db, id=highlight.id)
