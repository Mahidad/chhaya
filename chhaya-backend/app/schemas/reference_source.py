from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReferenceSourceCreate(BaseModel):
    """What the "Add source" screen submits."""
    title: str
    source_type: str  # "youtube_video" | "youtube_playlist" | "course_link"
    url: str


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    order_index: int
    duration_seconds: int | None
    transcript_status: str


class ReferenceSourceOut(BaseModel):
    """Used for both the list view and the polled detail view -- the
    frontend's "analysing" screen just polls this same shape until
    `status` flips to "ready" or "failed"."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    source_type: str
    url: str
    status: str
    error_message: str | None
    created_at: datetime
    videos: list[VideoOut] = []
