"""
The orchestration logic behind Feature 1 (Mahidad): add a source -> fetch
transcript(s) -> analyze style -> store one or more TeacherProfiles.

WHY THIS LIVES IN A SERVICE, NOT THE ROUTE:
The route (app/api/v1/endpoints/reference_sources.py) only knows about
HTTP: request in, response out. This function knows nothing about HTTP --
it takes a db connection and plain arguments, and could be called from a
route, a background worker, a CLI script, or a test, identically.

TWO CORNER CASES HANDLED HERE:

1. DUPLICATE LINKS. Before creating anything, both the single-video and
   playlist paths check whether this user already extracted this exact
   link (by URL) or, for single videos, this exact YouTube video id
   (catches the same video reached via a different URL format). If found
   and the caller didn't set `force=True`, this raises
   DuplicateSourceError -- the endpoint turns that into a 409 with enough
   detail for the frontend to ask "already extracted as '<title>' --
   extract again anyway?" and resubmit with force=True if the student
   says yes.

2. MULTIPLE TEACHERS IN ONE PLAYLIST. `_process_playlist` groups every
   video in the playlist by its uploader (channel_name, from
   utils/youtube_playlist.py), then runs the transcript-fetch ->
   style-analysis pipeline ONCE PER GROUP, not once for the whole
   playlist. A playlist mixing two instructors' channels produces two
   TeacherProfiles. This is a heuristic (same channel treated as same
   teacher), documented as such in utils/youtube_playlist.py.

CURRENT LIMITATION (documented, not hidden): this runs synchronously
inside the request. For a single video that's fine (a few seconds). For a
full playlist, this should become a background task (FastAPI
`BackgroundTasks`, or Celery once the team is comfortable with it) so the
"analysing" screen polls status instead of the request hanging. The
status field and polling GET endpoint are already built so that swap
doesn't change the API contract -- only what happens inside this function.
"""

from collections import defaultdict

import psycopg

from app.models.reference_source import ReferenceSource, SourceStatus, SourceType
from app.repositories.reference_source_repository import (
    reference_source_repository,
    video_repository,
)
from app.repositories.teacher_profile_repository import teacher_profile_repository
from app.schemas.reference_source import ReferenceSourceCreate
from app.services import preference_service
from app.services.teaching_style_service import analyze_style
from app.utils.exceptions import NotFoundError, DuplicateSourceError
from app.utils.youtube import extract_video_id, fetch_transcript_text, TranscriptUnavailableError
from app.utils.youtube_playlist import enumerate_playlist, PlaylistUnavailableError

# A combined transcript longer than this is truncated before being sent
# to Gemini -- keeps a big playlist group from blowing the prompt size or
# the per-call token cost.
MAX_COMBINED_TRANSCRIPT_CHARS = 15000


def create_and_process(
    db: psycopg.Connection, *, user_id: str, payload: ReferenceSourceCreate
) -> ReferenceSource:
    if payload.source_type == SourceType.YOUTUBE_PLAYLIST:
        return _process_playlist(db, user_id=user_id, payload=payload)
    if payload.source_type == SourceType.YOUTUBE_VIDEO:
        return _process_single_video(db, user_id=user_id, payload=payload)

    # course_link: genuinely not implemented. There's no generic API for
    # an arbitrary institutional LMS page the way there is for YouTube --
    # left honestly unsupported rather than faked.
    raise ValueError(
        "Course link ingestion isn't implemented yet -- only YouTube videos and playlists are supported."
    )


def _process_single_video(
    db: psycopg.Connection, *, user_id: str, payload: ReferenceSourceCreate
) -> ReferenceSource:
    video_id = extract_video_id(payload.url)

    if not payload.force:
        existing_video = video_repository.find_existing_video_for_user(
            db, user_id=user_id, youtube_video_id=video_id
        )
        if existing_video:
            raise DuplicateSourceError(
                existing_source_id=str(existing_video["existing_source_id"]),
                existing_title=existing_video["source_title"],
            )

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
        profile = teacher_profile_repository.create(
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

        for v in video_repository.list_for_source(db, source_id=source.id):
            video_repository.update(db, db_obj=v, obj_in={"teacher_profile_id": profile.id})

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

    if source.status == SourceStatus.READY:
        # A new profile just landed in the library -- the preference
        # profile's weighted average needs to include it. No-op (cheap)
        # if ingestion failed and no profile was actually created.
        preference_service.recompute_preference_profile(db, user_id=user_id)

    return reference_source_repository.get_for_user(db, source_id=source.id, user_id=user_id)


def _process_playlist(
    db: psycopg.Connection, *, user_id: str, payload: ReferenceSourceCreate
) -> ReferenceSource:
    if not payload.force:
        existing = reference_source_repository.find_existing_by_url(db, user_id=user_id, url=payload.url)
        if existing:
            raise DuplicateSourceError(existing_source_id=existing.id, existing_title=existing.title)

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

        entries = enumerate_playlist(payload.url)

        # Group by uploader -- this IS the multi-teacher detection. See
        # the module docstring above and utils/youtube_playlist.py.
        groups: dict[str, list[dict]] = defaultdict(list)
        for entry in entries:
            groups[entry["channel_name"]].append(entry)

        any_profile_created = False

        for channel_name, group_entries in groups.items():
            transcript_parts = []
            group_video_dicts = []

            for idx, entry in enumerate(group_entries):
                video_dict = {
                    "source_id": source.id,
                    "youtube_video_id": entry["video_id"],
                    "channel_name": channel_name,
                    "title": entry["title"],
                    "order_index": idx,
                    "duration_seconds": entry.get("duration_seconds"),
                    "transcript_status": SourceStatus.PENDING,
                }
                try:
                    text = fetch_transcript_text(entry["video_id"])
                    video_dict["transcript_text"] = text
                    video_dict["transcript_status"] = SourceStatus.READY
                    transcript_parts.append(text)
                except TranscriptUnavailableError:
                    # One video in the group failing doesn't sink the
                    # whole group -- partial success is real success here.
                    video_dict["transcript_status"] = SourceStatus.FAILED

                group_video_dicts.append(video_dict)

            created_videos = video_repository.bulk_create(db, videos=group_video_dicts)

            if not transcript_parts:
                continue  # every video in this group failed -- no profile for this group

            combined_text = " ".join(transcript_parts)[:MAX_COMBINED_TRANSCRIPT_CHARS]
            style = analyze_style(combined_text)

            profile = teacher_profile_repository.create(
                db,
                obj_in={
                    "user_id": user_id,
                    "source_id": source.id,
                    "channel_name": channel_name,
                    "display_name": f"{channel_name} — {payload.title}",
                    "pacing": style.get("pacing"),
                    "vocabulary_level": style.get("vocabulary_level"),
                    "analogy_frequency": style.get("analogy_frequency"),
                    "example_density": style.get("example_density"),
                    "raw_style_profile": style,
                },
            )
            any_profile_created = True

            for v in created_videos:
                video_repository.update(db, db_obj=v, obj_in={"teacher_profile_id": profile.id})

        if not any_profile_created:
            raise ValueError("Could not extract a transcript from any video in this playlist.")

        source = reference_source_repository.update(
            db, db_obj=source, obj_in={"status": SourceStatus.READY}
        )

    except PlaylistUnavailableError as exc:
        source = reference_source_repository.update(
            db, db_obj=source, obj_in={"status": SourceStatus.FAILED, "error_message": str(exc)}
        )
    except Exception as exc:  # noqa: BLE001
        source = reference_source_repository.update(
            db, db_obj=source, obj_in={"status": SourceStatus.FAILED, "error_message": str(exc)}
        )

    if source.status == SourceStatus.READY:
        # One or more new profiles just landed (one per detected
        # instructor) -- recompute once for all of them together rather
        # than once per profile inside the grouping loop above.
        preference_service.recompute_preference_profile(db, user_id=user_id)

    return reference_source_repository.get_for_user(db, source_id=source.id, user_id=user_id)


def get_source_for_user(
    db: psycopg.Connection, *, user_id: str, source_id: str
) -> ReferenceSource:
    source = reference_source_repository.get_for_user(
        db, source_id=source_id, user_id=user_id
    )
    if not source:
        raise NotFoundError("Reference source not found.")
    return source


def list_sources_for_user(
    db: psycopg.Connection, *, user_id: str
) -> list[ReferenceSource]:
    return reference_source_repository.list_for_user(db, user_id=user_id)


def delete_source(db: psycopg.Connection, *, user_id: str, source_id: str) -> None:
    source = get_source_for_user(db, user_id=user_id, source_id=source_id)
    reference_source_repository.delete(db, id=source.id)
