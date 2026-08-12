import psycopg
from psycopg.rows import dict_row

from app.models.code_style_profile import CodeStyleProfile
from app.repositories.base import BaseRepository


class CodeStyleProfileRepository(BaseRepository[CodeStyleProfile]):
    _table = "code_style_profiles"
    _model = CodeStyleProfile

    def list_for_user(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[CodeStyleProfile]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM code_style_profiles WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(
        self, db: psycopg.Connection, *, profile_id: str, user_id: str
    ) -> CodeStyleProfile | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM code_style_profiles WHERE id = %s AND user_id = %s",
                (profile_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


code_style_profile_repository = CodeStyleProfileRepository()
