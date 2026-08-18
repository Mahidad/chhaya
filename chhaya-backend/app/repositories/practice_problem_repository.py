import psycopg
from psycopg.rows import dict_row

from app.models.practice_problem import PracticeProblem
from app.repositories.base import BaseRepository


class PracticeProblemRepository(BaseRepository[PracticeProblem]):
    _table = "practice_problems"
    _model = PracticeProblem

    def list_by_difficulty(
        self, db: psycopg.Connection, *, difficulty: str, limit: int = 200
    ) -> list[PracticeProblem]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM practice_problems WHERE difficulty = %s ORDER BY title LIMIT %s",
                (difficulty, limit),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_by_slug(self, db: psycopg.Connection, *, title_slug: str) -> PracticeProblem | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM practice_problems WHERE title_slug = %s", (title_slug,))
            return self._row_to_obj(cur.fetchone())

    def get_many_by_slugs(
        self, db: psycopg.Connection, *, slugs: list[str]
    ) -> list[PracticeProblem]:
        """Used after Gemini picks which problems fit -- it returns slugs,
        and this fetches the real rows in one query rather than N."""
        if not slugs:
            return []
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM practice_problems WHERE title_slug = ANY(%s)", (slugs,))
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def count(self, db: psycopg.Connection) -> int:
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM practice_problems")
            return cur.fetchone()[0]


practice_problem_repository = PracticeProblemRepository()
