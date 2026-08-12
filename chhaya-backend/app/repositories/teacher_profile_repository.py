import psycopg
from psycopg.rows import dict_row

from app.models.teacher_profile import TeacherProfile
from app.repositories.base import BaseRepository


class TeacherProfileRepository(BaseRepository[TeacherProfile]):
    _table = "teacher_profiles"
    _model = TeacherProfile

    def get_by_source(
        self, db: psycopg.Connection, *, source_id: str
    ) -> TeacherProfile | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM teacher_profiles WHERE source_id = %s",
                (source_id,),
            )
            return self._row_to_obj(cur.fetchone())

    def list_by_source(
        self, db: psycopg.Connection, *, source_id: str
    ) -> list[TeacherProfile]:
        """Plural now -- a playlist source can have more than one profile,
        one per detected instructor. See app/services/reference_source_service.py."""
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM teacher_profiles WHERE source_id = %s ORDER BY created_at",
                (source_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def list_for_user(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[TeacherProfile]:
        """Returns profiles that the student has explicitly saved to their Style Library."""
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM teacher_profiles WHERE user_id = %s AND is_saved = TRUE ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]


teacher_profile_repository = TeacherProfileRepository()
