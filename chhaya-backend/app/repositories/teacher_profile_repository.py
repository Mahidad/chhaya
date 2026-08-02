from sqlalchemy.orm import Session

from app.models.teacher_profile import TeacherProfile
from app.repositories.base import BaseRepository


class TeacherProfileRepository(BaseRepository[TeacherProfile]):
    def get_by_source(self, db: Session, *, source_id: str) -> TeacherProfile | None:
        return db.query(TeacherProfile).filter(TeacherProfile.source_id == source_id).first()

    def list_for_user(self, db: Session, *, user_id: str) -> list[TeacherProfile]:
        return db.query(TeacherProfile).filter(TeacherProfile.user_id == user_id).all()


teacher_profile_repository = TeacherProfileRepository(TeacherProfile)
