import psycopg
from psycopg.rows import dict_row

from app.models.narration import Narration
from app.repositories.base import BaseRepository


class NarrationRepository(BaseRepository[Narration]):
    _table = "narrations"
    _model = Narration

    def list_for_content(
        self, db: psycopg.Connection, *, content_type: str, content_id: str, user_id: str
    ) -> list[Narration]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM narrations WHERE content_type = %s AND content_id = %s "
                "AND user_id = %s ORDER BY created_at DESC",
                (content_type, content_id, user_id),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(self, db: psycopg.Connection, *, narration_id: str, user_id: str) -> Narration | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM narrations WHERE id = %s AND user_id = %s",
                (narration_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


narration_repository = NarrationRepository()
