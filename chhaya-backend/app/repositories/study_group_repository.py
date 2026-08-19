"""Database queries for the Study Groups feature."""

import uuid

import psycopg
from psycopg.rows import dict_row

from app.models.study_group import (
    GroupInvitation,
    JoinRequest,
    StudyGroup,
    StudyGroupMember,
)
from app.repositories.base import BaseRepository


class StudyGroupRepository(BaseRepository[StudyGroup]):
    """Repository for study groups and their related membership records."""

    _table = "study_groups"
    _model = StudyGroup

    def create_with_creator(
        self,
        db: psycopg.Connection,
        *,
        creator_id: str,
        name: str,
        description: str,
    ) -> StudyGroup:
        group = self.create(
            db,
            obj_in={
                "creator_id": creator_id,
                "name": name,
                "description": description,
            },
        )
        self.add_member(db, group_id=group.id, user_id=creator_id)
        return group

    def list_for_user(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[StudyGroup]:
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
                   LEFT JOIN study_group_members mine
                          ON mine.group_id = g.id AND mine.user_id = %s
                   LEFT JOIN study_group_join_requests join_request
                          ON join_request.group_id = g.id
                         AND join_request.user_id = %s
                   GROUP BY g.id, u.full_name, mine.user_id, join_request.status
                   ORDER BY g.created_at DESC""",
                (user_id, user_id),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(
        self, db: psycopg.Connection, *, group_id: str, user_id: str
    ) -> StudyGroup | None:
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
                   LEFT JOIN study_group_members mine
                          ON mine.group_id = g.id AND mine.user_id = %s
                   LEFT JOIN study_group_join_requests join_request
                          ON join_request.group_id = g.id
                         AND join_request.user_id = %s
                   WHERE g.id = %s
                   GROUP BY g.id, u.full_name, mine.user_id, join_request.status""",
                (user_id, user_id, group_id),
            )
            return self._row_to_obj(cur.fetchone())

    def list_members(
        self, db: psycopg.Connection, *, group_id: str
    ) -> list[StudyGroupMember]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """SELECT u.id AS user_id, u.full_name, u.email
                   FROM study_group_members m
                   JOIN users u ON u.id = m.user_id
                   WHERE m.group_id = %s
                   ORDER BY u.full_name""",
                (group_id,),
            )
            return [StudyGroupMember(**row) for row in cur.fetchall()]

    def create_invitation(
        self,
        db: psycopg.Connection,
        *,
        group_id: str,
        invited_user_id: str,
        invited_by_user_id: str,
    ) -> None:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO study_group_invitations
                   (id, group_id, invited_user_id, invited_by_user_id)
                   VALUES (%s, %s, %s, %s)""",
                (str(uuid.uuid4()), group_id, invited_user_id, invited_by_user_id),
            )

    def list_invitations(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[GroupInvitation]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """SELECT i.*, g.name AS group_name,
                          g.description AS group_description,
                          u.full_name AS invited_by_name, i.status, i.created_at
                   FROM study_group_invitations i
                   JOIN study_groups g ON g.id = i.group_id
                   JOIN users u ON u.id = i.invited_by_user_id
                   WHERE i.invited_user_id = %s
                   ORDER BY i.created_at DESC""",
                (user_id,),
            )
            return [GroupInvitation(**row) for row in cur.fetchall()]

    def get_invitation(
        self, db: psycopg.Connection, *, invitation_id: str, user_id: str
    ) -> GroupInvitation | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """SELECT * FROM study_group_invitations
                   WHERE id = %s AND invited_user_id = %s""",
                (invitation_id, user_id),
            )
            row = cur.fetchone()
            return GroupInvitation(**row) if row else None

    def update_invitation(
        self, db: psycopg.Connection, *, invitation_id: str, status: str
    ) -> None:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE study_group_invitations SET status = %s WHERE id = %s",
                (status, invitation_id),
            )

    def add_member(
        self, db: psycopg.Connection, *, group_id: str, user_id: str
    ) -> None:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO study_group_members (group_id, user_id)
                   VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                (group_id, user_id),
            )

    def create_join_request(
        self, db: psycopg.Connection, *, group_id: str, user_id: str
    ) -> None:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO study_group_join_requests (id, group_id, user_id)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (group_id, user_id) DO NOTHING""",
                (str(uuid.uuid4()), group_id, user_id),
            )

    def list_join_requests(
        self, db: psycopg.Connection, *, group_id: str
    ) -> list[JoinRequest]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """SELECT r.*, u.full_name, u.email
                   FROM study_group_join_requests r
                   JOIN users u ON u.id = r.user_id
                   WHERE r.group_id = %s AND r.status = 'pending'
                   ORDER BY r.created_at""",
                (group_id,),
            )
            return [JoinRequest(**row) for row in cur.fetchall()]

    def get_join_request(
        self, db: psycopg.Connection, *, request_id: str, group_id: str
    ) -> JoinRequest | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """SELECT * FROM study_group_join_requests
                   WHERE id = %s AND group_id = %s""",
                (request_id, group_id),
            )
            row = cur.fetchone()
            return JoinRequest(**row) if row else None

    def update_join_request(
        self, db: psycopg.Connection, *, request_id: str, status: str
    ) -> None:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE study_group_join_requests SET status = %s WHERE id = %s",
                (status, request_id),
            )


study_group_repository = StudyGroupRepository()
