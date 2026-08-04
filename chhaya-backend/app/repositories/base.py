"""
Generic CRUD base — raw psycopg v3.

Subclasses declare two class-level attributes:
    _table : str           -- PostgreSQL table name (a hardcoded constant,
                              never user input, so f-string interpolation is safe)
    _model : type          -- Python dataclass to hydrate DB rows into

Inherited operations: get / create / update / delete.
Domain-specific queries (list_for_user, get_by_email, …) live only in the
relevant subclass, exactly as before.

COMMIT POLICY:
  None of these methods commit.  The single commit happens in `get_db()`
  (app/core/database.py) after the entire request handler succeeds, giving
  all-or-nothing semantics across multi-step service pipelines without any
  extra work here.

JSON / JSONB:
  Any dict value in obj_in is wrapped in psycopg's `Jsonb` adapter so the
  driver serialises it as JSON rather than Python repr.  This covers
  `raw_style_profile` in teacher_profiles transparently.
"""

import uuid
from typing import Generic, TypeVar, Type

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    _table: str           # set by every subclass
    _model: Type[ModelType]  # set by every subclass

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _row_to_obj(self, row: dict | None) -> ModelType | None:
        """Convert a dict_row from psycopg into the target dataclass."""
        if row is None:
            return None
        return self._model(**row)

    @staticmethod
    def _wrap_json(data: dict) -> dict:
        """
        Wrap any dict-typed value in Jsonb so psycopg sends it as JSON
        to a JSONB column.  Non-dict values (str, int, bool, None …)
        pass through unchanged.
        """
        return {
            k: Jsonb(v) if isinstance(v, dict) else v
            for k, v in data.items()
        }

    # ------------------------------------------------------------------ #
    #  Generic CRUD                                                        #
    # ------------------------------------------------------------------ #

    def get(self, db: psycopg.Connection, id: str) -> ModelType | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"SELECT * FROM {self._table} WHERE id = %s",
                (id,),
            )
            return self._row_to_obj(cur.fetchone())

    def create(self, db: psycopg.Connection, *, obj_in: dict) -> ModelType:
        # Always generate the PK client-side so RETURNING * gives us the
        # full row (including server defaults such as created_at) without
        # a separate SELECT.
        data = self._wrap_json({"id": str(uuid.uuid4()), **obj_in})
        cols = list(data.keys())
        sql = (
            f"INSERT INTO {self._table} ({', '.join(cols)}) "
            f"VALUES ({', '.join(['%s'] * len(cols))}) "
            f"RETURNING *"
        )
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, [data[c] for c in cols])
            return self._row_to_obj(cur.fetchone())

    def update(
        self, db: psycopg.Connection, *, db_obj: ModelType, obj_in: dict
    ) -> ModelType:
        data = self._wrap_json(obj_in)
        set_clauses = [f"{col} = %s" for col in data.keys()]
        values = list(data.values()) + [db_obj.id]
        sql = (
            f"UPDATE {self._table} "
            f"SET {', '.join(set_clauses)} "
            f"WHERE id = %s "
            f"RETURNING *"
        )
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, values)
            return self._row_to_obj(cur.fetchone())

    def delete(self, db: psycopg.Connection, *, id: str) -> None:
        with db.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table} WHERE id = %s",
                (id,),
            )
