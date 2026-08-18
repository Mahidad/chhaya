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


code_visualization_repository = CodeVisualizationRepository()
