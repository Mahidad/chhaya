import os

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.voice_narration import VoiceNarrationCreate, VoiceNarrationOut
from app.services import voice_narration_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/voice-narrations", tags=["voice-narrations"])


@router.post("", response_model=VoiceNarrationOut, status_code=status.HTTP_201_CREATED)
def create_narration(
    payload: VoiceNarrationCreate,
    regenerate: bool = False,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates narration for a note or a study guide.

    Returns the EXISTING narration if one is already saved for that
    source -- per the spec, audio is kept unless explicitly regenerated.
    Pass `?regenerate=true` to discard the saved audio and synthesise a
    fresh one (e.g. after the student edits the note, or picks a
    different teacher's voice).
    """
    try:
        return voice_narration_service.create_narration(
            db, user_id=current_user.id, payload=payload, regenerate=regenerate
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=VoiceNarrationOut | None)
def find_existing_narration(
    note_id: str | None = None,
    study_guide_id: str | None = None,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    "Is there already audio for this note/guide?" -- lets the page decide
    whether to show a play button or a generate button, without kicking
    off generation just by loading. Returns null when there's nothing yet.
    """
    if not note_id and not study_guide_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide note_id or study_guide_id.",
        )
    return voice_narration_service.find_existing(
        db, user_id=current_user.id, note_id=note_id, study_guide_id=study_guide_id
    )


@router.get("/{narration_id}", response_model=VoiceNarrationOut)
def get_narration(
    narration_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return voice_narration_service.get_narration_for_user(
            db, user_id=current_user.id, narration_id=narration_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{narration_id}/audio")
def get_narration_audio(
    narration_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Serves the mp3 -- same pattern as notes serving their uploaded
    files (see endpoints/notes.py's /{note_id}/file)."""
    try:
        narration = voice_narration_service.get_narration_for_user(
            db, user_id=current_user.id, narration_id=narration_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not narration.audio_path or not os.path.exists(narration.audio_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found on disk."
        )

    return FileResponse(narration.audio_path, media_type="audio/mpeg")


@router.delete("/{narration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_narration(
    narration_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        voice_narration_service.delete_narration(
            db, user_id=current_user.id, narration_id=narration_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
