"""
Routes for Module 2's Word Lookup & Personal Glossary (Lamia).
GET /dictionary/{word} is the zero-API-call lookup described in the
feature spec; everything else is plain CRUD against glossary_entries.
"""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.glossary import (
    DictionaryLookupOut, GlossaryEntryCreate, GlossaryEntryUpdate, GlossaryEntryOut,
)
from app.services import glossary_service
from app.utils.exceptions import NotFoundError

router = APIRouter(tags=["glossary"])


@router.get("/dictionary/{word}", response_model=DictionaryLookupOut)
def define_word(word: str, topic: str | None = None):
    """
    A local WordNet or Gemini dictionary query (see app/utils/dictionary.py).
    Passes optional `topic` context to get domain-specific definitions (e.g. OOP vs biology).
    """
    return glossary_service.lookup_word(word, topic=topic)


@router.post("/glossary", response_model=GlossaryEntryOut, status_code=status.HTTP_201_CREATED)
def save_glossary_entry(
    payload: GlossaryEntryCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return glossary_service.save_glossary_entry(
            db, user_id=current_user.id, chapter_id=payload.chapter_id, term=payload.term,
            definition=payload.definition, part_of_speech=payload.part_of_speech, source=payload.source,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/glossary", response_model=list[GlossaryEntryOut])
def list_glossary(
    chapter_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return glossary_service.list_glossary_for_chapter(db, user_id=current_user.id, chapter_id=chapter_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/glossary/{entry_id}", response_model=GlossaryEntryOut)
def update_glossary_entry(
    entry_id: str,
    payload: GlossaryEntryUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return glossary_service.update_glossary_entry(
            db, user_id=current_user.id, entry_id=entry_id, definition=payload.definition
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/glossary/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary_entry(
    entry_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        glossary_service.delete_glossary_entry(db, user_id=current_user.id, entry_id=entry_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
