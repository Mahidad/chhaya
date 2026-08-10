import psycopg
from psycopg.rows import dict_row

from app.models.exam_paper import ExamPaper
from app.repositories.base import BaseRepository


class ExamPaperRepository(BaseRepository[ExamPaper]):
    _table = "exam_papers"
    _model = ExamPaper

    def list_for_user(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[ExamPaper]:
        with db.cursor(row_factory=dict_row) as cur:  #A cursor is like a tool used to send SQL commands.
            cur.execute(
                "SELECT * FROM exam_papers WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(
        self, db: psycopg.Connection, *, paper_id: str, user_id: str
    ) -> ExamPaper | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM exam_papers WHERE id = %s AND user_id = %s",
                (paper_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


exam_paper_repository = ExamPaperRepository()
