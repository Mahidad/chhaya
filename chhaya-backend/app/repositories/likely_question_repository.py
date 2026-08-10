import psycopg
from psycopg.rows import dict_row

from app.models.likely_question import LikelyQuestionSet
from app.repositories.base import BaseRepository


class LikelyQuestionRepository(BaseRepository[LikelyQuestionSet]):
    _table = "likely_questions"
    _model = LikelyQuestionSet

    def list_for_user(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[LikelyQuestionSet]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM likely_questions WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(
        self, db: psycopg.Connection, *, set_id: str, user_id: str
    ) -> LikelyQuestionSet | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM likely_questions WHERE id = %s AND user_id = %s",
                (set_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


likely_question_repository = LikelyQuestionRepository()
