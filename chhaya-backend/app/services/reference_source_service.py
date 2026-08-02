"""
The orchestration logic behind Feature 1 (Mahidad): add a source -> fetch
transcript -> analyze style -> store a TeacherProfile.

WHY THIS LIVES IN A SERVICE, NOT THE ROUTE:
The route (app/api/v1/endpoints/reference_sources.py) only knows about
HTTP: request in, response out. This function knows nothing about HTTP --
it takes a db session and plain arguments, and could be called from a
route, a background worker, a CLI script, or a test, identically.

CURRENT LIMITATION (documented, not hidden): this runs synchronously
inside the request. For a single video that's fine (a few seconds). For a
full playlist, this should become a background task (FastAPI
`BackgroundTasks`, or Celery once the team is comfortable with it) so the
"analysing" screen polls status instead of the request hanging. The
status field and polling GET endpoint are already built so that swap
doesn't change the API contract -- only what happens inside this function.
"""

from sqlalchemy.orm import Session

from app.models.reference_source import ReferenceSource, SourceStatus
from app.repositories.reference_source_repository import (
    reference_source_repository,
    video_repository,
)
from app.repositories.teacher_profile_repository import teacher_profile_repository
from app.schemas.reference_source import ReferenceSourceCreate
from app.services.teaching_style_service import analyze_style
from app.utils.exceptions import NotFoundError
from app.utils.youtube import extract_video_id, fetch_transcript_text, TranscriptUnavailableError


def create_and_process(db: Session, *, user_id: str, payload: ReferenceSourceCreate) -> ReferenceSource:
    source = reference_source_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "title": payload.title,
            "source_type": payload.source_type,
            "url": payload.url,
            "status": SourceStatus.PENDING,
        },
    )

    try:
        source = reference_source_repository.update(
            db, db_obj=source, obj_in={"status": SourceStatus.PROCESSING}
        )

        # NOTE: playlist crawling (many videos) is intentionally out of
        # scope for this first pass -- see docstring above. Single video
        # today; TODO extend to enumerate playlist entries.
        video_id = extract_video_id(payload.url)
        transcript_text = fetch_transcript_text(video_id)

        video_repository.bulk_create(
            db,
            videos=[
                {
                    "source_id": source.id,
                    "youtube_video_id": video_id,
                    "title": payload.title,
                    "order_index": 0,
                    "transcript_text": transcript_text,
                    "transcript_status": SourceStatus.READY,
                }
            ],
        )

        style = analyze_style(transcript_text)
        teacher_profile_repository.create(
            db,
            obj_in={
                "user_id": user_id,
                "source_id": source.id,
                "display_name": payload.title,
                "pacing": style.get("pacing"),
                "vocabulary_level": style.get("vocabulary_level"),
                "analogy_frequency": style.get("analogy_frequency"),
                "example_density": style.get("example_density"),
                "raw_style_profile": style,
            },
        )

        source = reference_source_repository.update(
            db, db_obj=source, obj_in={"status": SourceStatus.READY}
        )

    except TranscriptUnavailableError as exc:
        source = reference_source_repository.update(
            db, db_obj=source, obj_in={"status": SourceStatus.FAILED, "error_message": str(exc)}
        )
    except Exception as exc:  # noqa: BLE001 - ingestion must never crash the request unhandled
        source = reference_source_repository.update(
            db, db_obj=source, obj_in={"status": SourceStatus.FAILED, "error_message": str(exc)}
        )

    return source


def get_source_for_user(db: Session, *, user_id: str, source_id: str) -> ReferenceSource:
    source = reference_source_repository.get_for_user(db, source_id=source_id, user_id=user_id)
    if not source:
        raise NotFoundError("Reference source not found.")
    return source


def list_sources_for_user(db: Session, *, user_id: str) -> list[ReferenceSource]:
    return reference_source_repository.list_for_user(db, user_id=user_id)


def delete_source(db: Session, *, user_id: str, source_id: str) -> None:
    source = get_source_for_user(db, user_id=user_id, source_id=source_id)  # raises if not found/not yours
    reference_source_repository.delete(db, id=source.id)
