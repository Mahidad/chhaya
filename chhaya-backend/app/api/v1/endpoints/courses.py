"""
Routes for Module 2's Course/Chapter organization (Lamia). Two routers in
one file: `router` (mounted at /courses) for course-level operations and
the course->chapters nesting, and `chapters_router` (mounted at /chapters)
for chapter-level operations that don't need the course id in the path
once you already have the chapter id. Both get registered in
app/api/v1/api.py, same as every other feature's router(s).

ROUTE ORDERING NOTE: `/courses/reorder` and
`/courses/{course_id}/chapters/reorder` are declared *before* the matching
`/{course_id}` route below them. FastAPI matches path routes in the order
they're registered, so if a route with `{course_id}` came first, a
request to `/courses/reorder` would be matched by it with
`course_id="reorder"` instead of ever reaching the reorder route.
"""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseOut,
    ChapterCreate, ChapterUpdate, ChapterOut,
    ReorderRequest,
)
from app.schemas.study_guide import StudyGuideOut
from app.schemas.note import NoteOut
from app.services import course_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/courses", tags=["courses"])
chapters_router = APIRouter(prefix="/chapters", tags=["chapters"])


# --------------------------------------------------------------------------
# Courses
# --------------------------------------------------------------------------

@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return course_service.create_course(db, user_id=current_user.id, title=payload.title)


@router.get("", response_model=list[CourseOut])
def list_courses(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return course_service.list_courses_for_user(db, user_id=current_user.id)


@router.patch("/reorder", response_model=list[CourseOut])
def reorder_courses(
    payload: ReorderRequest,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return course_service.reorder_courses(db, user_id=current_user.id, ordered_ids=payload.ordered_ids)


@router.get("/{course_id}", response_model=CourseOut)
def get_course(
    course_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return course_service.get_course_for_user(db, user_id=current_user.id, course_id=course_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{course_id}", response_model=CourseOut)
def rename_course(
    course_id: str,
    payload: CourseUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return course_service.rename_course(db, user_id=current_user.id, course_id=course_id, title=payload.title)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        course_service.delete_course(db, user_id=current_user.id, course_id=course_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# --------------------------------------------------------------------------
# Chapters, nested under a course
# --------------------------------------------------------------------------

@router.post("/{course_id}/chapters", response_model=ChapterOut, status_code=status.HTTP_201_CREATED)
def create_chapter(
    course_id: str,
    payload: ChapterCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return course_service.create_chapter(db, user_id=current_user.id, course_id=course_id, title=payload.title)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{course_id}/chapters", response_model=list[ChapterOut])
def list_chapters(
    course_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return course_service.list_chapters_for_course(db, user_id=current_user.id, course_id=course_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{course_id}/chapters/reorder", response_model=list[ChapterOut])
def reorder_chapters(
    course_id: str,
    payload: ReorderRequest,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return course_service.reorder_chapters(
            db, user_id=current_user.id, course_id=course_id, ordered_ids=payload.ordered_ids
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# --------------------------------------------------------------------------
# Chapters, standalone (no course_id needed once you have the chapter id)
# --------------------------------------------------------------------------

@chapters_router.get("/{chapter_id}", response_model=ChapterOut)
def get_chapter(
    chapter_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return course_service.get_chapter_for_user(db, user_id=current_user.id, chapter_id=chapter_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@chapters_router.patch("/{chapter_id}", response_model=ChapterOut)
def rename_chapter(
    chapter_id: str,
    payload: ChapterUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return course_service.rename_chapter(db, user_id=current_user.id, chapter_id=chapter_id, title=payload.title)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@chapters_router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(
    chapter_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        course_service.delete_chapter(db, user_id=current_user.id, chapter_id=chapter_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@chapters_router.get("/{chapter_id}/contents")
def get_chapter_contents(
    chapter_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    No response_model here on purpose: this returns a mixed shape
    (`{chapter, study_guides, notes}`), not a single schema type. Each
    piece is still converted through its own *_Out schema below, so the
    same "never leak DB-only fields like file_path" rule from every other
    endpoint still applies -- it just happens by hand instead of via
    FastAPI's automatic response_model conversion.
    """
    try:
        result = course_service.get_chapter_contents(db, user_id=current_user.id, chapter_id=chapter_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return {
        "chapter": ChapterOut.model_validate(result["chapter"]),
        "study_guides": [StudyGuideOut.model_validate(g) for g in result["study_guides"]],
        "notes": [NoteOut.model_validate(n) for n in result["notes"]],
    }
