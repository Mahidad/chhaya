import psycopg
from psycopg.rows import dict_row

from app.models.annotation import Highlight
from app.repositories.base import BaseRepository


class HighlightRepository(BaseRepository[Highlight]):
    _table = "highlights"
    _model = Highlight

    def list_for_content(
        self, db: psycopg.Connection, *, content_type: str, content_id: str, user_id: str
    ) -> list[Highlight]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM highlights WHERE content_type = %s AND content_id = %s "
                "AND user_id = %s ORDER BY created_at ASC",
                (content_type, content_id, user_id),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(self, db: psycopg.Connection, *, highlight_id: str, user_id: str) -> Highlight | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM highlights WHERE id = %s AND user_id = %s",
                (highlight_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


highlight_repository = HighlightRepository()
