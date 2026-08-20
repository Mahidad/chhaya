import psycopg
from psycopg.rows import dict_row

from app.models.code_visualization import CodeVisualization
from app.repositories.base import BaseRepository


class CodeVisualizationRepository(BaseRepository[CodeVisualization]):
    _table = "code_visualizations"
    _model = CodeVisualization

    def list_for_user(self, db: psycopg.Connection, *, user_id: str) -> list[CodeVisualization]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM code_visualizations WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(self, db: psycopg.Connection, *, visualization_id: str, user_id: str) -> CodeVisualization | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM code_visualizations WHERE id = %s AND user_id = %s",
                (visualization_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())

    def find_identical(
        self, db: psycopg.Connection, *, user_id: str, language: str, source_code: str
    ) -> "CodeVisualization | None":
        """The row this request would duplicate, if there is one.

        Same reasoning as CodeConversionRepository.find_identical: tracing
        the same code in the same language twice should refresh one row, not
        stack up copies in whichever folder it was filed into. Oldest match
        wins so the organised row is the one kept.
        """
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM code_visualizations
                WHERE user_id = %s AND language = %s AND source_code = %s
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (user_id, language, source_code),
            )
            return self._row_to_obj(cur.fetchone())


code_visualization_repository = CodeVisualizationRepository()
