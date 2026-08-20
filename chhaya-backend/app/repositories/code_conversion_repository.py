import psycopg
from psycopg.rows import dict_row

from app.models.code_conversion import CodeConversion
from app.repositories.base import BaseRepository


class CodeConversionRepository(BaseRepository[CodeConversion]):
    _table = "code_conversions"
    _model = CodeConversion

    def list_for_user(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[CodeConversion]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM code_conversions WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(
        self, db: psycopg.Connection, *, conversion_id: str, user_id: str
    ) -> CodeConversion | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM code_conversions WHERE id = %s AND user_id = %s",
                (conversion_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())

    def find_identical(
        self,
        db: psycopg.Connection,
        *,
        user_id: str,
        mode: str,
        target_language: str,
        source_code: str | None,
        problem_statement: str | None,
    ) -> CodeConversion | None:
        """The row this request would duplicate, if there is one.

        IDENTITY IS (user, mode, inputs, target language). Deliberately NOT
        the style profile: re-translating the same source with a different
        coding style is the same piece of work rendered differently, not a
        second file, and treating it as new is what left two identical-
        looking rows sitting in the same folder. The re-run overwrites, and
        the row keeps the folder and title it was already given.

        Target language IS part of identity -- one source translated to Java
        and to Python are two different results, so those stay separate.

        IS NOT DISTINCT FROM rather than = because source_code is NULL on
        solve rows and problem_statement is NULL on translate rows, and
        `NULL = NULL` is NULL, not true.

        Returns the OLDEST match, so re-running keeps folder and title on
        the row the user already organised rather than on a newer copy.
        """
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM code_conversions
                WHERE user_id = %s
                  AND mode = %s
                  AND target_language = %s
                  AND source_code IS NOT DISTINCT FROM %s
                  AND problem_statement IS NOT DISTINCT FROM %s
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (user_id, mode, target_language, source_code, problem_statement),
            )
            return self._row_to_obj(cur.fetchone())


code_conversion_repository = CodeConversionRepository()
