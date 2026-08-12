from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CourseCreate(BaseModel):
    title: str


class CourseUpdate(BaseModel):
    title: str


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    order_index: int
    created_at: datetime


class ChapterCreate(BaseModel):
    title: str


class ChapterUpdate(BaseModel):
    title: str


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_id: str
    title: str
    order_index: int
    created_at: datetime


class ReorderRequest(BaseModel):
    """
    Body for both `PATCH /courses/reorder` and
    `PATCH /courses/{course_id}/chapters/reorder`: the full list of ids in
    their new order. Simpler than a per-item "move to index N" endpoint --
    the frontend already has the whole list in memory after the student
    reorders it, so it just sends the new order back whole.
    """
    ordered_ids: list[str]
