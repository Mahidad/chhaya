"""
ReferenceSource and Video dataclasses — replace the SQLAlchemy ORM models.

Key design note on `videos`:
  The old ORM model used a SQLAlchemy `relationship` to lazily load the
  child Video rows.  Here that field is a plain Python list that the
  repository populates explicitly with a second query after fetching the
  parent row(s).  Because it has a default (`field(default_factory=list)`)
  it is absent from INSERT/UPDATE dicts, so the base repository never
  tries to write it to the database.

  `ReferenceSourceOut.videos` is declared with `from_attributes=True`, so
  Pydantic reads `source.videos` directly off the dataclass instance —
  no change required in the schema layer.
"""

from dataclasses import dataclass, field
from datetime import datetime


class SourceStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class SourceType:
    YOUTUBE_VIDEO = "youtube_video"
    YOUTUBE_PLAYLIST = "youtube_playlist"
    COURSE_LINK = "course_link"


@dataclass
class ReferenceSource:
    id: str
    user_id: str
    title: str
    source_type: str
    url: str
    status: str
    created_at: datetime
    # Nullable columns — default to None so `ReferenceSource(**db_row)`
    # works when the DB returns NULL for these columns.
    error_message: str | None = None
    # Populated by the repository after fetching; never written to DB.
    videos: list = field(default_factory=list)


@dataclass
class Video:
    id: str
    source_id: str
    youtube_video_id: str
    title: str
    transcript_status: str
    order_index: int = 0
    duration_seconds: int | None = None
    transcript_text: str | None = None
