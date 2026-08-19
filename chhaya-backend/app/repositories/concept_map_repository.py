import psycopg
from psycopg.rows import dict_row

from app.models.concept_map import ConceptMap
from app.repositories.base import BaseRepository


class ConceptMapRepository(BaseRepository[ConceptMap]):
    _table = "concept_maps"
    _model = ConceptMap

    def list_for_user(self, db: psycopg.Connection, *, user_id: str) -> list[ConceptMap]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM concept_maps WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(
        self, db: psycopg.Connection, *, concept_map_id: str, user_id: str
    ) -> ConceptMap | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM concept_maps WHERE id = %s AND user_id = %s",
                (concept_map_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


concept_map_repository = ConceptMapRepository()
