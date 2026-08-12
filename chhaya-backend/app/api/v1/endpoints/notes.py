"""
Routes for Module 2's Import/Upload Personal Notes (Lamia). Follows the
exact multipart/form-data shape as POST /exam-papers (see
api/v1/endpoints/exam_papers.py) -- even a plain text note goes through
Form(...) fields, not a JSON body, so one endpoint handles all three note
types (text/image/pdf) uniformly instead of branching between a JSON
route and a separate file-upload route.
"""

import os

import psycopg
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.note import NoteType
from app.models.user import User
from app.schemas.note import NoteOut, NoteUpdate
from app.services import note_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    chapter_id: str = Form(...),
    title: str = Form(...),
    note_type: str = Form(NoteType.TEXT),
    text_content: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read() if file else None
    try:
        return note_service.create_note(
            db,
            user_id=current_user.id,
            chapter_id=chapter_id,
            title=title,
            note_type=note_type,
            text_content=text_content,
            file_bytes=file_bytes,
            filename=file.filename if file else None,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[NoteOut])
def list_notes(
    chapter_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return note_service.list_notes_for_chapter(db, user_id=current_user.id, chapter_id=chapter_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return note_service.get_note_for_user(db, user_id=current_user.id, note_id=note_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: str,
    payload: NoteUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return note_service.update_note(
            db, user_id=current_user.id, note_id=note_id,
            title=payload.title, text_content=payload.text_content,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        note_service.delete_note(db, user_id=current_user.id, note_id=note_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{note_id}/file")
def get_note_file(
    note_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        note = note_service.get_note_for_user(db, user_id=current_user.id, note_id=note_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not note.file_path or not os.path.exists(note.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk.")

    ext = os.path.splitext(note.file_path)[1].lower()
    media_type = "application/pdf" if ext == ".pdf" else f"image/{ext.lstrip('.') or 'png'}"
    return FileResponse(note.file_path, media_type=media_type)
