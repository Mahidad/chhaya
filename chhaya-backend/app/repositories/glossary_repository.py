import psycopg
from psycopg.rows import dict_row

from app.models.glossary import GlossaryEntry
from app.repositories.base import BaseRepository


class GlossaryRepository(BaseRepository[GlossaryEntry]):
    _table = "glossary_entries"
    _model = GlossaryEntry

    def list_for_chapter(self, db: psycopg.Connection, *, chapter_id: str, user_id: str) -> list[GlossaryEntry]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM glossary_entries WHERE chapter_id = %s AND user_id = %s ORDER BY term ASC",
                (chapter_id, user_id),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(self, db: psycopg.Connection, *, entry_id: str, user_id: str) -> GlossaryEntry | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM glossary_entries WHERE id = %s AND user_id = %s",
                (entry_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


glossary_repository = GlossaryRepository()
