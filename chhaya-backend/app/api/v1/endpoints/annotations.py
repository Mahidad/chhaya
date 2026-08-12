"""
Routes for Module 2's Highlights (Lamia).
"""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.annotation import HighlightCreate, HighlightOut
from app.services import annotation_service
from app.utils.exceptions import NotFoundError

router = APIRouter(tags=["annotations"])


# --------------------------------------------------------------------------
# Highlights
# --------------------------------------------------------------------------

@router.post("/highlights", response_model=HighlightOut, status_code=status.HTTP_201_CREATED)
def create_highlight(
    payload: HighlightCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return annotation_service.create_highlight(
            db, user_id=current_user.id, chapter_id=payload.chapter_id,
            content_type=payload.content_type, content_id=payload.content_id,
            quoted_text=payload.quoted_text, color=payload.color,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/highlights", response_model=list[HighlightOut])
def list_highlights(
    content_type: str,
    content_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return annotation_service.list_highlights_for_content(
        db, user_id=current_user.id, content_type=content_type, content_id=content_id
    )


@router.delete("/highlights/{highlight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_highlight(
    highlight_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        annotation_service.delete_highlight(db, user_id=current_user.id, highlight_id=highlight_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
