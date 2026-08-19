"""
Orchestration for Module 3's AI Voice Narration (Lamia):
  1. Look up the source content (a study guide or a text note) and check
     the student actually owns it.
  2. Resolve which teaching style to read it in -- the guide's own
     profile by default, or an explicitly chosen one for a note (which
     has no inherent style of its own).
  3. Gemini rewrites the source text into phrasing that reads well aloud
     (narration_generation_service.py).
  4. edge-tts synthesizes that text into an MP3 (app/utils/tts.py),
     using a voice + speaking rate resolved from the teaching style.
  5. Save the audio file to disk and the row to status=ready, same
     try/except-to-FAILED shape used by every other AI pipeline in this
     app (study_guide_service.create_and_generate,
     reference_source_service.create_and_process).
"""

import os
import uuid

import psycopg

from app.core.config import settings
from app.models.annotation import ContentType
from app.models.narration import Narration, NarrationStatus
from app.repositories.narration_repository import narration_repository
from app.repositories.study_guide_repository import study_guide_repository
from app.repositories.note_repository import note_repository
from app.repositories.teacher_profile_repository import teacher_profile_repository
from app.services.narration_generation_service import rewrite_for_narration
from app.utils.exceptions import NotFoundError
from app.utils.tts import rate_for_pacing, synthesize, DEFAULT_VOICE

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "narrations"
)


def _get_owned_content(db: psycopg.Connection, *, user_id: str, content_type: str, content_id: str):
    """Same ownership-check shape as annotation_service._assert_owns_content
    -- content_id has no real foreign key (see models/annotation.py), so
    every feature that touches it re-checks ownership itself."""
    if content_type == ContentType.STUDY_GUIDE:
        item = study_guide_repository.get(db, content_id)
    elif content_type == ContentType.NOTE:
        item = note_repository.get(db, content_id)
    else:
        raise ValueError(f"Unknown content_type: {content_type}")

    if not item or item.user_id != user_id:
        raise NotFoundError("The content you're trying to narrate was not found.")
    return item


def create_and_generate(
    db: psycopg.Connection, *, user_id: str, content_type: str, content_id: str,
    teacher_profile_id: str | None,
) -> Narration:
    content = _get_owned_content(db, user_id=user_id, content_type=content_type, content_id=content_id)

    # Resolve source text + which teaching style to read it in.
    if content_type == ContentType.STUDY_GUIDE:
        source_text = content.content
        # A guide already has its own style -- use it unless the caller
        # explicitly picked a different one.
        resolved_profile_id = teacher_profile_id or content.teacher_profile_id
    else:
        if content.note_type != "text" or not content.text_content:
            raise ValueError("Only text notes can be narrated (image and PDF notes have no text to read).")
        source_text = content.text_content
        # A note has no inherent teaching style -- the caller must choose one.
        if not teacher_profile_id:
            raise ValueError("Choose a teacher's style to narrate this note in.")
        resolved_profile_id = teacher_profile_id

    if not source_text or not source_text.strip():
        raise ValueError("There's no text here to narrate yet.")

    profile = None
    if resolved_profile_id:
        profile = teacher_profile_repository.get(db, resolved_profile_id)
        if not profile or profile.user_id != user_id:
            raise NotFoundError("That teacher style profile was not found in your library.")
    style = (profile.raw_style_profile if profile else None) or {}

    voice = profile.narration_voice if profile else DEFAULT_VOICE
    rate = rate_for_pacing(style)

    narration = narration_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "content_type": content_type,
            "content_id": content_id,
            "teacher_profile_id": profile.id if profile else None,
            "voice": voice,
            "rate": rate,
            "status": NarrationStatus.PENDING,
        },
    )

    try:
        narration = narration_repository.update(
            db, db_obj=narration, obj_in={"status": NarrationStatus.GENERATING}
        )

        narration_text = rewrite_for_narration(text=source_text, style=style)
        text_was_mock = not settings.GEMINI_API_KEY

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        target_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.mp3")
        actual_path, audio_was_mock = synthesize(narration_text, voice, rate, target_path)

        narration = narration_repository.update(
            db,
            db_obj=narration,
            obj_in={
                "narration_text": narration_text,
                "audio_path": actual_path,
                "is_mock": text_was_mock or audio_was_mock,
                "status": NarrationStatus.READY,
            },
        )
    except Exception as exc:  # noqa: BLE001
        narration = narration_repository.update(
            db, db_obj=narration, obj_in={"status": NarrationStatus.FAILED, "error_message": str(exc)}
        )

    return narration


def list_narrations_for_content(
    db: psycopg.Connection, *, user_id: str, content_type: str, content_id: str
) -> list[Narration]:
    return narration_repository.list_for_content(
        db, content_type=content_type, content_id=content_id, user_id=user_id
    )


def get_narration_for_user(db: psycopg.Connection, *, user_id: str, narration_id: str) -> Narration:
    narration = narration_repository.get_for_user(db, narration_id=narration_id, user_id=user_id)
    if not narration:
        raise NotFoundError("Narration not found.")
    return narration


def delete_narration(db: psycopg.Connection, *, user_id: str, narration_id: str) -> None:
    narration = get_narration_for_user(db, user_id=user_id, narration_id=narration_id)
    if narration.audio_path and os.path.exists(narration.audio_path):
        try:
            os.remove(narration.audio_path)
        except OSError:
            pass
    narration_repository.delete(db, id=narration.id)
