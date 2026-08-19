"""Direct, simple PostgreSQL queries for study-group messages."""

import uuid
import psycopg
from psycopg.rows import dict_row


def is_member(db: psycopg.Connection, *, group_id: str, user_id: str) -> bool:
    with db.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM study_group_members WHERE group_id = %s AND user_id = %s",
            (group_id, user_id),
        )
        return cur.fetchone() is not None


def list_messages(db: psycopg.Connection, *, group_id: str) -> list[dict]:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT m.*, u.full_name AS author_name,
                      pinner.full_name AS pinned_by_name
               FROM study_group_messages m JOIN users u ON u.id = m.user_id
               LEFT JOIN users pinner ON pinner.id = m.pinned_by_user_id
               WHERE m.group_id = %s
               ORDER BY m.is_pinned DESC, m.created_at ASC""",
            (group_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def create_message(db: psycopg.Connection, *, group_id: str, user_id: str, content: str) -> dict:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """INSERT INTO study_group_messages (id, group_id, user_id, content)
               VALUES (%s, %s, %s, %s)
               RETURNING *""",
            (str(uuid.uuid4()), group_id, user_id, content),
        )
        message = dict(cur.fetchone())
        cur.execute("SELECT full_name FROM users WHERE id = %s", (user_id,))
        message["author_name"] = cur.fetchone()["full_name"]
        message["pinned_by_name"] = None
        return message


def get_message(db: psycopg.Connection, *, message_id: str, group_id: str) -> dict | None:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM study_group_messages WHERE id = %s AND group_id = %s",
            (message_id, group_id),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def set_pinned(db: psycopg.Connection, *, message_id: str, pinned: bool, user_id: str) -> None:
    with db.cursor() as cur:
        cur.execute(
            """UPDATE study_group_messages
               SET is_pinned = %s, pinned_by_user_id = %s
               WHERE id = %s""",
            (pinned, user_id if pinned else None, message_id),
        )
