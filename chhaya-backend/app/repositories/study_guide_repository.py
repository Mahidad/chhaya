import psycopg
from psycopg.rows import dict_row

from app.models.study_guide import StudyGuide
from app.repositories.base import BaseRepository


class StudyGuideRepository(BaseRepository[StudyGuide]):
    _table = "study_guides"
    _model = StudyGuide

    def list_for_user(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[StudyGuide]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM study_guides WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(
        self, db: psycopg.Connection, *, guide_id: str, user_id: str
    ) -> StudyGuide | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM study_guides WHERE id = %s AND user_id = %s",
                (guide_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())

    def list_for_chapter(
        self, db: psycopg.Connection, *, chapter_id: str, user_id: str
    ) -> list[StudyGuide]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM study_guides WHERE chapter_id = %s AND user_id = %s ORDER BY created_at DESC",
                (chapter_id, user_id),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]


study_guide_repository = StudyGuideRepository()
