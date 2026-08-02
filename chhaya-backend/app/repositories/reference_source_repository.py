from sqlalchemy.orm import Session

from app.models.reference_source import ReferenceSource, Video
from app.repositories.base import BaseRepository


class ReferenceSourceRepository(BaseRepository[ReferenceSource]):
    def get_for_user(self, db: Session, *, source_id: str, user_id: str) -> ReferenceSource | None:
        """Scoping every lookup by user_id here (not just in the route) means
        a bug in one route can't accidentally leak another student's data --
        the repository itself refuses to return rows that aren't yours."""
        return (
            db.query(ReferenceSource)
            .filter(ReferenceSource.id == source_id, ReferenceSource.user_id == user_id)
            .first()
        )

    def list_for_user(self, db: Session, *, user_id: str) -> list[ReferenceSource]:
        return (
            db.query(ReferenceSource)
            .filter(ReferenceSource.user_id == user_id)
            .order_by(ReferenceSource.created_at.desc())
            .all()
        )


class VideoRepository(BaseRepository[Video]):
    def bulk_create(self, db: Session, *, videos: list[dict]) -> list[Video]:
        objs = [Video(**v) for v in videos]
        db.add_all(objs)
        db.commit()
        for obj in objs:
            db.refresh(obj)
        return objs


reference_source_repository = ReferenceSourceRepository(ReferenceSource)
video_repository = VideoRepository(Video)
