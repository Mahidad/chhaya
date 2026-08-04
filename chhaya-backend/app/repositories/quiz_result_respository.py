import psycopg
from psycopg.rows import dict_row

from app.models.quiz_result import QuizResult
from app.repositories.base import BaseRepository


class QuizResultRepository(BaseRepository[QuizResult]):
    _table = "quiz_results"
    _model = QuizResult

    def list_for_user(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[QuizResult]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM quiz_results WHERE user_id = %s ORDER BY taken_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]


quiz_result_repository = QuizResultRepository()
