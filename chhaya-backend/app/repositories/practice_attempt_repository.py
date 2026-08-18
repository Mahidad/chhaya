import psycopg
from psycopg.rows import dict_row

from app.models.practice_attempt import PracticeAttempt
from app.repositories.base import BaseRepository


class PracticeAttemptRepository(BaseRepository[PracticeAttempt]):
    _table = "practice_attempts"
    _model = PracticeAttempt

    def list_for_user(self, db: psycopg.Connection, *, user_id: str) -> list[PracticeAttempt]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM practice_attempts WHERE user_id = %s ORDER BY started_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(
        self, db: psycopg.Connection, *, attempt_id: str, user_id: str
    ) -> PracticeAttempt | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM practice_attempts WHERE id = %s AND user_id = %s",
                (attempt_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())

    def list_solved_slugs_for_user(self, db: psycopg.Connection, *, user_id: str) -> list[str]:
        """Feeds the "don't suggest what they've already solved" filter in
        practice_service.suggest_problems."""
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT pp.title_slug
                FROM practice_attempts pa
                JOIN practice_problems pp ON pp.id = pa.problem_id
                WHERE pa.user_id = %s AND pa.is_correct = TRUE
                """,
                (user_id,),
            )
            return [row[0] for row in cur.fetchall()]


practice_attempt_repository = PracticeAttemptRepository()
