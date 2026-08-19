"""
Routes for Module 3's AI Voice Narration (Lamia).
"""

import os

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.narration import NarrationCreate, NarrationOut, VoiceOption
from app.services import narration_service
from app.utils.exceptions import NotFoundError
from app.utils.tts import list_available_voices

router = APIRouter(tags=["narrations"])


@router.get("/voices", response_model=list[VoiceOption])
def get_available_voices():
    """The short curated voice list students pick from -- see
    app/utils/tts.py's AVAILABLE_VOICES for why it's a handful, not
    every voice Edge offers."""
    return list_available_voices()


@router.post("/narrations", response_model=NarrationOut, status_code=status.HTTP_201_CREATED)
def create_narration(
    payload: NarrationCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return narration_service.create_and_generate(
            db,
            user_id=current_user.id,
            content_type=payload.content_type,
            content_id=payload.content_id,
            teacher_profile_id=payload.teacher_profile_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/narrations", response_model=list[NarrationOut])
def list_narrations(
    content_type: str,
    content_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return narration_service.list_narrations_for_content(
        db, user_id=current_user.id, content_type=content_type, content_id=content_id
    )


@router.get("/narrations/{narration_id}", response_model=NarrationOut)
def get_narration(
    narration_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return narration_service.get_narration_for_user(db, user_id=current_user.id, narration_id=narration_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/narrations/{narration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_narration(
    narration_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        narration_service.delete_narration(db, user_id=current_user.id, narration_id=narration_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/narrations/{narration_id}/audio")
def get_narration_audio(
    narration_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        narration = narration_service.get_narration_for_user(db, user_id=current_user.id, narration_id=narration_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not narration.audio_path or not os.path.exists(narration.audio_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found on disk.")

    # .mp3 in the normal case; .wav in mock mode (see app/utils/tts.py's
    # _mock_synthesize) -- media_type follows whatever's actually on disk.
    ext = os.path.splitext(narration.audio_path)[1].lower()
    media_type = "audio/wav" if ext == ".wav" else "audio/mpeg"
    return FileResponse(narration.audio_path, media_type=media_type)
