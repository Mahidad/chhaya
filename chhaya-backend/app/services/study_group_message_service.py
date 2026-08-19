"""Membership checks and actions for study-group discussion messages."""

import psycopg

from app.models.study_group_message import StudyGroupMessage
from app.repositories.study_group_message_repository import study_group_message_repository
from app.utils.exceptions import NotFoundError, PermissionDeniedError


def _require_member(db: psycopg.Connection, *, group_id: str, user_id: str) -> None:
    if not study_group_message_repository.is_member(
        db, group_id=group_id, user_id=user_id
    ):
        raise PermissionDeniedError("Only group members can access this discussion.")


def list_messages(
    db: psycopg.Connection, *, group_id: str, user_id: str
) -> list[StudyGroupMessage]:
    _require_member(db, group_id=group_id, user_id=user_id)
    return study_group_message_repository.list_for_group(db, group_id=group_id)


def post_message(
    db: psycopg.Connection, *, group_id: str, user_id: str, content: str
) -> StudyGroupMessage:
    _require_member(db, group_id=group_id, user_id=user_id)
    return study_group_message_repository.create_for_group(
        db,
        group_id=group_id,
        user_id=user_id,
        content=content.strip(),
    )


def change_pin(
    db: psycopg.Connection,
    *,
    group_id: str,
    message_id: str,
    user_id: str,
    pinned: bool,
) -> None:
    _require_member(db, group_id=group_id, user_id=user_id)
    message = study_group_message_repository.get_for_group(
        db, message_id=message_id, group_id=group_id
    )
    if not message:
        raise NotFoundError("Message not found.")
    study_group_message_repository.update_pin(
        db,
        message=message,
        pinned=pinned,
        user_id=user_id,
    )
