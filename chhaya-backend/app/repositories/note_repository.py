import psycopg
from psycopg.rows import dict_row

from app.models.note import Note
from app.repositories.base import BaseRepository


class NoteRepository(BaseRepository[Note]):
    _table = "notes"
    _model = Note

    def list_for_chapter(self, db: psycopg.Connection, *, chapter_id: str, user_id: str) -> list[Note]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM notes WHERE chapter_id = %s AND user_id = %s ORDER BY created_at DESC",
                (chapter_id, user_id),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(self, db: psycopg.Connection, *, note_id: str, user_id: str) -> Note | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM notes WHERE id = %s AND user_id = %s",
                (note_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


note_repository = NoteRepository()
