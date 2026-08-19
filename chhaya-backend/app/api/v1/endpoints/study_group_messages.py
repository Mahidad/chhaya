"""Discussion routes. Every route is restricted to group members."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.study_group_message import MessageCreate, MessageOut
from app.services import study_group_message_service
from app.utils.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/study-groups/{group_id}/messages", tags=["study-group-messages"])


def _error(exc: Exception):
    code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_403_FORBIDDEN
    raise HTTPException(status_code=code, detail=str(exc))


@router.get("", response_model=list[MessageOut])
def list_group_messages(
    group_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return study_group_message_service.list_messages(db, group_id=group_id, user_id=current_user.id)
    except PermissionDeniedError as exc:
        _error(exc)


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def post_group_message(
    group_id: str,
    payload: MessageCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return study_group_message_service.post_message(
            db, group_id=group_id, user_id=current_user.id, content=payload.content
        )
    except PermissionDeniedError as exc:
        _error(exc)


@router.post("/{message_id}/pin", status_code=status.HTTP_204_NO_CONTENT)
def pin_message(
    group_id: str,
    message_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        study_group_message_service.change_pin(
            db, group_id=group_id, message_id=message_id, user_id=current_user.id, pinned=True
        )
    except (NotFoundError, PermissionDeniedError) as exc:
        _error(exc)


@router.post("/{message_id}/unpin", status_code=status.HTTP_204_NO_CONTENT)
def unpin_message(
    group_id: str,
    message_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        study_group_message_service.change_pin(
            db, group_id=group_id, message_id=message_id, user_id=current_user.id, pinned=False
        )
    except (NotFoundError, PermissionDeniedError) as exc:
        _error(exc)
