"""
Orchestration for Module 3 Feature 1 (Lamia): voice narration of notes
and study guides.

TWO RULES FROM THE SPEC ENFORCED HERE:

1. "The generated voice will be saved unless regenerated." A narration is
   reused if one already exists for that note/guide -- `create_narration`
   returns the existing row rather than re-synthesising. Passing
   `regenerate=True` deletes the old audio file and makes a fresh one, so
   the student explicitly opts into the cost rather than paying it on
   every page visit.

2. "Choosing a teacher's style will not be available for generated
   guides." A study guide already carries `teacher_profile_id`, so its
   narration inherits that profile automatically. The request schema
   rejects a client-supplied profile for guides (see
   schemas/voice_narration.py), and this service reads the guide's own
   profile instead -- so the two can never disagree.

Runs synchronously, same as every other generation pipeline in this app
(see reference_source_service.py's docstring for the reasoning and what
would change to move it to a background task).
"""

import os

import psycopg

from app.models.voice_narration import NarrationStatus
from app.repositories.note_repository import note_repository
from app.repositories.study_guide_repository import study_guide_repository
from app.repositories.teacher_profile_repository import teacher_profile_repository
from app.repositories.voice_narration_repository import voice_narration_repository
from app.schemas.voice_narration import VoiceNarrationCreate
from app.utils import tts
from app.utils.exceptions import NotFoundError

# Same convention as note_service.UPLOAD_DIR / exam_paper_service.UPLOAD_DIR.
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "uploads",
    "voice_narrations",
)


def _resolve_source(db: psycopg.Connection, *, user_id: str, payload: VoiceNarrationCreate):
    """
    Returns (text_to_narrate, teacher_profile_or_None).

    For a note: the student's own text, narrated in whichever teacher
    style they picked (or a neutral default if they picked none).
    For a guide: the guide's content, narrated in the guide's OWN
    teacher profile -- not a user-supplied one.
    """
    if payload.note_id:
        note = note_repository.get_for_user(db, note_id=payload.note_id, user_id=user_id)
        if not note:
            raise NotFoundError("Note not found.")
        if not note.text_content or not note.text_content.strip():
            raise NotFoundError(
                "That note has no text to narrate -- only text notes can be turned into audio."
            )

        profile = None
        if payload.teacher_profile_id:
            profile = teacher_profile_repository.get(db, payload.teacher_profile_id)
            if not profile or str(profile.user_id) != str(user_id):
                raise NotFoundError("Teacher style profile not found.")
        return note.text_content, profile

    guide = study_guide_repository.get_for_user(db, guide_id=payload.study_guide_id, user_id=user_id)
    if not guide:
        raise NotFoundError("Study guide not found.")
    if not guide.content or not guide.content.strip():
        raise NotFoundError("That study guide has no content to narrate yet.")

    # Inherit the guide's own style -- see rule 2 in the module docstring.
    profile = teacher_profile_repository.get(db, guide.teacher_profile_id)
    return guide.content, profile


def _delete_audio_file(path: str | None) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def create_narration(
    db: psycopg.Connection, *, user_id: str, payload: VoiceNarrationCreate, regenerate: bool = False
):
    existing = (
        voice_narration_repository.get_for_note(db, note_id=payload.note_id, user_id=user_id)
        if payload.note_id
        else voice_narration_repository.get_for_study_guide(
            db, study_guide_id=payload.study_guide_id, user_id=user_id
        )
    )

    if existing and existing.status == NarrationStatus.READY and not regenerate:
        return existing

    text, profile = _resolve_source(db, user_id=user_id, payload=payload)
    voice, rate = tts.select_voice(profile)

    if existing:
        # Regenerating: reuse the row, drop the stale audio file.
        _delete_audio_file(existing.audio_path)
        narration = voice_narration_repository.update(
            db,
            db_obj=existing,
            obj_in={
                "status": NarrationStatus.GENERATING,
                "teacher_profile_id": profile.id if profile else None,
                "voice_short_name": voice,
                "rate": rate,
                "audio_path": None,
                "error_message": None,
                "duration_seconds": None,
            },
        )
    else:
        narration = voice_narration_repository.create(
            db,
            obj_in={
                "user_id": user_id,
                "note_id": payload.note_id,
                "study_guide_id": payload.study_guide_id,
                "teacher_profile_id": profile.id if profile else None,
                "voice_short_name": voice,
                "rate": rate,
                "status": NarrationStatus.GENERATING,
            },
        )

    try:
        audio_path = tts.generate_audio(text=text, voice=voice, rate=rate, upload_dir=UPLOAD_DIR)
        narration = voice_narration_repository.update(
            db,
            db_obj=narration,
            obj_in={
                "status": NarrationStatus.READY,
                "audio_path": audio_path,
                "duration_seconds": tts.estimate_duration_seconds(text, rate),
            },
        )
    except Exception as exc:  # noqa: BLE001
        narration = voice_narration_repository.update(
            db,
            db_obj=narration,
            obj_in={"status": NarrationStatus.FAILED, "error_message": str(exc)},
        )

    return narration


def get_narration_for_user(db: psycopg.Connection, *, user_id: str, narration_id: str):
    narration = voice_narration_repository.get_for_user(
        db, narration_id=narration_id, user_id=user_id
    )
    if not narration:
        raise NotFoundError("Narration not found.")
    return narration


def find_existing(db: psycopg.Connection, *, user_id: str, note_id: str | None, study_guide_id: str | None):
    """Lets the frontend check "is there already audio for this?" on page
    load without triggering generation."""
    if note_id:
        return voice_narration_repository.get_for_note(db, note_id=note_id, user_id=user_id)
    if study_guide_id:
        return voice_narration_repository.get_for_study_guide(
            db, study_guide_id=study_guide_id, user_id=user_id
        )
    return None


def delete_narration(db: psycopg.Connection, *, user_id: str, narration_id: str) -> None:
    narration = get_narration_for_user(db, user_id=user_id, narration_id=narration_id)
    _delete_audio_file(narration.audio_path)
    voice_narration_repository.delete(db, id=narration.id)
