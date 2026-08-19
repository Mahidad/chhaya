"""Database queries for messages inside study groups."""

import psycopg
from psycopg.rows import dict_row

from app.models.study_group_message import StudyGroupMessage
from app.repositories.base import BaseRepository


class StudyGroupMessageRepository(BaseRepository[StudyGroupMessage]):
    """Repository for study-group messages and their pin status."""

    _table = "study_group_messages"
    _model = StudyGroupMessage

    def is_member(
        self, db: psycopg.Connection, *, group_id: str, user_id: str
    ) -> bool:
        with db.cursor() as cur:
            cur.execute(
                """SELECT 1 FROM study_group_members
                   WHERE group_id = %s AND user_id = %s""",
                (group_id, user_id),
            )
            return cur.fetchone() is not None

    def list_for_group(
        self, db: psycopg.Connection, *, group_id: str
    ) -> list[StudyGroupMessage]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """SELECT m.*, u.full_name AS author_name,
                          pinner.full_name AS pinned_by_name
                   FROM study_group_messages m
                   JOIN users u ON u.id = m.user_id
                   LEFT JOIN users pinner ON pinner.id = m.pinned_by_user_id
                   WHERE m.group_id = %s
                   ORDER BY m.is_pinned DESC, m.created_at ASC""",
                (group_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_group(
        self, db: psycopg.Connection, *, message_id: str, group_id: str
    ) -> StudyGroupMessage | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """SELECT * FROM study_group_messages
                   WHERE id = %s AND group_id = %s""",
                (message_id, group_id),
            )
            return self._row_to_obj(cur.fetchone())

    def get_with_author(
        self, db: psycopg.Connection, *, message_id: str
    ) -> StudyGroupMessage | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """SELECT m.*, u.full_name AS author_name,
                          pinner.full_name AS pinned_by_name
                   FROM study_group_messages m
                   JOIN users u ON u.id = m.user_id
                   LEFT JOIN users pinner ON pinner.id = m.pinned_by_user_id
                   WHERE m.id = %s""",
                (message_id,),
            )
            return self._row_to_obj(cur.fetchone())

    def create_for_group(
        self,
        db: psycopg.Connection,
        *,
        group_id: str,
        user_id: str,
        content: str,
    ) -> StudyGroupMessage:
        message = self.create(
            db,
            obj_in={
                "group_id": group_id,
                "user_id": user_id,
                "content": content,
            },
        )
        message_with_author = self.get_with_author(db, message_id=message.id)
        if not message_with_author:
            raise RuntimeError("Created study-group message could not be loaded.")
        return message_with_author

    def update_pin(
        self,
        db: psycopg.Connection,
        *,
        message: StudyGroupMessage,
        pinned: bool,
        user_id: str,
    ) -> StudyGroupMessage:
        return self.update(
            db,
            db_obj=message,
            obj_in={
                "is_pinned": pinned,
                "pinned_by_user_id": user_id if pinned else None,
            },
        )


study_group_message_repository = StudyGroupMessageRepository()
