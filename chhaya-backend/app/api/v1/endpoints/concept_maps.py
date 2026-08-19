"""
Routes for Module 3's Concept Map active-recall game (Lamia).
"""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.concept_map import (
    ConceptMapCreate, ConceptMapOut, ConceptMapAttemptCreate, ConceptMapAttemptOut,
)
from app.services import concept_map_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/concept-maps", tags=["concept-maps"])


@router.post("", response_model=ConceptMapOut, status_code=status.HTTP_201_CREATED)
def create_concept_map(
    payload: ConceptMapCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return concept_map_service.create_and_generate(
            db, user_id=current_user.id, title=payload.title, extraction_mode=payload.extraction_mode,
            chapter_id=payload.chapter_id, source_study_guide_id=payload.source_study_guide_id,
            raw_text=payload.raw_text,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[ConceptMapOut])
def list_concept_maps(
    chapter_id: str | None = None,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if chapter_id:
        try:
            return concept_map_service.list_maps_for_chapter(db, user_id=current_user.id, chapter_id=chapter_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return concept_map_service.list_maps_for_user(db, user_id=current_user.id)


@router.get("/{map_id}", response_model=ConceptMapOut)
def get_concept_map(
    map_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return concept_map_service.get_map_for_user(db, user_id=current_user.id, map_id=map_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{map_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept_map(
    map_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        concept_map_service.delete_map(db, user_id=current_user.id, map_id=map_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{map_id}/attempts", response_model=ConceptMapAttemptOut, status_code=status.HTTP_201_CREATED)
def create_attempt(
    map_id: str,
    payload: ConceptMapAttemptCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return concept_map_service.record_attempt(
            db, user_id=current_user.id, map_id=map_id,
            correct_count=payload.correct_count, total_count=payload.total_count,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{map_id}/attempts", response_model=list[ConceptMapAttemptOut])
def list_attempts(
    map_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return concept_map_service.list_attempts_for_map(db, user_id=current_user.id, map_id=map_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
