"""Request and response shapes for group discussions."""

from datetime import datetime
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class MessageOut(BaseModel):
    id: str
    group_id: str
    user_id: str
    author_name: str
    content: str
    is_pinned: bool
    pinned_by_name: str | None
    created_at: datetime
