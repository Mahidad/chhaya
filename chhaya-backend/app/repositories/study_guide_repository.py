from sqlalchemy.orm import Session
from app.models.study_guide import StudyGuide
from app.repositories.base import BaseRepository


class StudyGuideRepository(BaseRepository[StudyGuide]):
    def list_for_user(self, db: Session, *, user_id: str) -> list[StudyGuide]:
        return (
            db.query(StudyGuide)
            .filter(StudyGuide.user_id == user_id)
            .order_by(StudyGuide.created_at.desc())
            .all()
        )

    def get_for_user(self, db: Session, *, guide_id: str, user_id: str) -> StudyGuide | None:
        return (
            db.query(StudyGuide)
            .filter(StudyGuide.id == guide_id, StudyGuide.user_id == user_id)
            .first()
        )


study_guide_repository = StudyGuideRepository(StudyGuide)
