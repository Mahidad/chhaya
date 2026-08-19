import json

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.models.concept_map import ConceptMap, ConceptMapAttempt
from app.repositories.base import BaseRepository


class ConceptMapRepository(BaseRepository[ConceptMap]):
    _table = "concept_maps"
    _model = ConceptMap

    def _row_to_obj(self, row):
        if row is None:
            return None
        # `items` comes back from psycopg as a Python list already
        # (JSONB auto-decodes) -- but guard against the rare case it
        # arrives as a raw JSON string, same defensive shape used
        # anywhere else in this codebase that stores JSONB.
        if isinstance(row.get("items"), str):
            row["items"] = json.loads(row["items"])
        return super()._row_to_obj(row)

    def create(self, db: psycopg.Connection, *, obj_in: dict):
        obj_in = {**obj_in, "items": Jsonb(obj_in["items"])}
        return super().create(db, obj_in=obj_in)

    def list_for_user(self, db: psycopg.Connection, *, user_id: str) -> list[ConceptMap]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM concept_maps WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def list_for_chapter(self, db: psycopg.Connection, *, chapter_id: str, user_id: str) -> list[ConceptMap]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM concept_maps WHERE chapter_id = %s AND user_id = %s ORDER BY created_at DESC",
                (chapter_id, user_id),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(self, db: psycopg.Connection, *, map_id: str, user_id: str) -> ConceptMap | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM concept_maps WHERE id = %s AND user_id = %s",
                (map_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


class ConceptMapAttemptRepository(BaseRepository[ConceptMapAttempt]):
    _table = "concept_map_attempts"
    _model = ConceptMapAttempt

    def list_for_map(self, db: psycopg.Connection, *, concept_map_id: str, user_id: str) -> list[ConceptMapAttempt]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM concept_map_attempts WHERE concept_map_id = %s AND user_id = %s "
                "ORDER BY completed_at DESC",
                (concept_map_id, user_id),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]


concept_map_repository = ConceptMapRepository()
concept_map_attempt_repository = ConceptMapAttemptRepository()
