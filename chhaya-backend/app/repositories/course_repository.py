import psycopg
from psycopg.rows import dict_row

from app.models.course import Course, Chapter
from app.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    _table = "courses"
    _model = Course

    def list_for_user(self, db: psycopg.Connection, *, user_id: str) -> list[Course]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM courses WHERE user_id = %s ORDER BY order_index ASC, created_at ASC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(self, db: psycopg.Connection, *, course_id: str, user_id: str) -> Course | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM courses WHERE id = %s AND user_id = %s",
                (course_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())

    def next_order_index(self, db: psycopg.Connection, *, user_id: str) -> int:
        with db.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(order_index), -1) + 1 FROM courses WHERE user_id = %s",
                (user_id,),
            )
            return cur.fetchone()[0]


class ChapterRepository(BaseRepository[Chapter]):
    _table = "chapters"
    _model = Chapter

    def list_for_course(self, db: psycopg.Connection, *, course_id: str, user_id: str) -> list[Chapter]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM chapters WHERE course_id = %s AND user_id = %s "
                "ORDER BY order_index ASC, created_at ASC",
                (course_id, user_id),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(self, db: psycopg.Connection, *, chapter_id: str, user_id: str) -> Chapter | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM chapters WHERE id = %s AND user_id = %s",
                (chapter_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())

    def next_order_index(self, db: psycopg.Connection, *, course_id: str) -> int:
        with db.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(order_index), -1) + 1 FROM chapters WHERE course_id = %s",
                (course_id,),
            )
            return cur.fetchone()[0]


course_repository = CourseRepository()
chapter_repository = ChapterRepository()
