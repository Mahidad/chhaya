"""Small, direct SQL queries for study groups.

This repository deliberately keeps the SQL visible and simple for beginners.
"""

import uuid
import psycopg
from psycopg.rows import dict_row


def _one(cur):
    row = cur.fetchone()
    return dict(row) if row else None


def create_group(db: psycopg.Connection, *, creator_id: str, name: str, description: str) -> dict:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """INSERT INTO study_groups (id, creator_id, name, description)
               VALUES (%s, %s, %s, %s) RETURNING *""",
            (str(uuid.uuid4()), creator_id, name, description),
        )
        group = _one(cur)
        cur.execute(
            """INSERT INTO study_group_members (group_id, user_id)
               VALUES (%s, %s)""",
            (group["id"], creator_id),
        )
        return group


def list_groups(db: psycopg.Connection, *, user_id: str) -> list[dict]:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT g.*, u.full_name AS creator_name,
                      COUNT(m.user_id)::int AS member_count,
                      CASE WHEN mine.user_id IS NOT NULL THEN 'member'
                           WHEN join_request.status = 'pending' THEN 'requested'
                           ELSE NULL END AS membership_status
               FROM study_groups g
               JOIN users u ON u.id = g.creator_id
               LEFT JOIN study_group_members m ON m.group_id = g.id
               LEFT JOIN study_group_members mine ON mine.group_id = g.id AND mine.user_id = %s
               LEFT JOIN study_group_join_requests join_request ON join_request.group_id = g.id AND join_request.user_id = %s
               GROUP BY g.id, u.full_name, mine.user_id, join_request.status
               ORDER BY g.created_at DESC""",
            (user_id, user_id),
        )
        return [dict(row) for row in cur.fetchall()]


def get_group(db: psycopg.Connection, *, group_id: str, user_id: str) -> dict | None:
    groups = list_groups(db, user_id=user_id)
    return next((group for group in groups if group["id"] == group_id), None)


def list_members(db: psycopg.Connection, *, group_id: str) -> list[dict]:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT u.id AS user_id, u.full_name, u.email
               FROM study_group_members m JOIN users u ON u.id = m.user_id
               WHERE m.group_id = %s ORDER BY u.full_name""",
            (group_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def create_invitation(db: psycopg.Connection, *, group_id: str, invited_user_id: str, invited_by_user_id: str) -> None:
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO study_group_invitations (id, group_id, invited_user_id, invited_by_user_id)
               VALUES (%s, %s, %s, %s)""",
            (str(uuid.uuid4()), group_id, invited_user_id, invited_by_user_id),
        )


def list_invitations(db: psycopg.Connection, *, user_id: str) -> list[dict]:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT i.id, i.group_id, g.name AS group_name, g.description AS group_description,
                      u.full_name AS invited_by_name, i.status, i.created_at
               FROM study_group_invitations i
               JOIN study_groups g ON g.id = i.group_id
               JOIN users u ON u.id = i.invited_by_user_id
               WHERE i.invited_user_id = %s ORDER BY i.created_at DESC""",
            (user_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_invitation(db: psycopg.Connection, *, invitation_id: str, user_id: str) -> dict | None:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM study_group_invitations WHERE id = %s AND invited_user_id = %s",
            (invitation_id, user_id),
        )
        return _one(cur)


def update_invitation(db: psycopg.Connection, *, invitation_id: str, status: str) -> None:
    with db.cursor() as cur:
        cur.execute("UPDATE study_group_invitations SET status = %s WHERE id = %s", (status, invitation_id))


def add_member(db: psycopg.Connection, *, group_id: str, user_id: str) -> None:
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO study_group_members (group_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (group_id, user_id),
        )


def create_join_request(db: psycopg.Connection, *, group_id: str, user_id: str) -> None:
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO study_group_join_requests (id, group_id, user_id)
               VALUES (%s, %s, %s) ON CONFLICT (group_id, user_id) DO NOTHING""",
            (str(uuid.uuid4()), group_id, user_id),
        )


def list_join_requests(db: psycopg.Connection, *, group_id: str) -> list[dict]:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT r.id, r.user_id, u.full_name, u.email, r.status, r.created_at
               FROM study_group_join_requests r JOIN users u ON u.id = r.user_id
               WHERE r.group_id = %s AND r.status = 'pending' ORDER BY r.created_at""",
            (group_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_join_request(db: psycopg.Connection, *, request_id: str, group_id: str) -> dict | None:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM study_group_join_requests WHERE id = %s AND group_id = %s",
            (request_id, group_id),
        )
        return _one(cur)


def update_join_request(db: psycopg.Connection, *, request_id: str, status: str) -> None:
    with db.cursor() as cur:
        cur.execute("UPDATE study_group_join_requests SET status = %s WHERE id = %s", (status, request_id))


def delete_group(db: psycopg.Connection, *, group_id: str) -> None:
    with db.cursor() as cur:
        cur.execute("DELETE FROM study_groups WHERE id = %s", (group_id,))
