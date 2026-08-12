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


code_conversion_repository = CodeConversionRepository()
