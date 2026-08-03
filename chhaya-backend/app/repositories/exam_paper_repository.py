from sqlalchemy.orm import Session
from app.models.exam_paper import ExamPaper
from app.repositories.base import BaseRepository


class ExamPaperRepository(BaseRepository[ExamPaper]):
    def list_for_user(self, db: Session, *, user_id: str) -> list[ExamPaper]:
        return (
            db.query(ExamPaper)
            .filter(ExamPaper.user_id == user_id)
            .order_by(ExamPaper.created_at.desc())
            .all()
        )

    def get_for_user(self, db: Session, *, paper_id: str, user_id: str) -> ExamPaper | None:
        return (
            db.query(ExamPaper)
            .filter(ExamPaper.id == paper_id, ExamPaper.user_id == user_id)
            .first()
        )


exam_paper_repository = ExamPaperRepository(ExamPaper)
