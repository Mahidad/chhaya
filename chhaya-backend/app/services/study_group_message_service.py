"""Membership checks and basic actions for group discussion messages."""

import psycopg

from app.repositories import study_group_message_repository as repo
from app.utils.exceptions import NotFoundError, PermissionDeniedError


def _require_member(db: psycopg.Connection, *, group_id: str, user_id: str) -> None:
    if not repo.is_member(db, group_id=group_id, user_id=user_id):
        raise PermissionDeniedError("Only group members can access this discussion.")


def list_messages(db: psycopg.Connection, *, group_id: str, user_id: str) -> list[dict]:
    _require_member(db, group_id=group_id, user_id=user_id)
    return repo.list_messages(db, group_id=group_id)


def post_message(db: psycopg.Connection, *, group_id: str, user_id: str, content: str) -> dict:
    _require_member(db, group_id=group_id, user_id=user_id)
    return repo.create_message(db, group_id=group_id, user_id=user_id, content=content.strip())


def change_pin(db: psycopg.Connection, *, group_id: str, message_id: str, user_id: str, pinned: bool) -> None:
    _require_member(db, group_id=group_id, user_id=user_id)
    message = repo.get_message(db, message_id=message_id, group_id=group_id)
    if not message:
        raise NotFoundError("Message not found.")
    repo.set_pinned(db, message_id=message_id, pinned=pinned, user_id=user_id)
