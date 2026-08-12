"""
Orchestration for Module 2's organizational backbone (Lamia): Courses and
Chapters. No AI/external calls here at all -- this is the plain CRUD +
reorder shape, the simplest of the four new Module 2 features, deliberately
kept that way since its whole job is to be a reliable filing cabinet for
everything else (study guides, notes, highlights, sticky notes, glossary).
"""

import psycopg

from app.models.course import Course, Chapter
from app.repositories.course_repository import course_repository, chapter_repository
from app.repositories.study_guide_repository import study_guide_repository
from app.repositories.note_repository import note_repository
from app.utils.exceptions import NotFoundError


# --------------------------------------------------------------------------
# Courses
# --------------------------------------------------------------------------

def create_course(db: psycopg.Connection, *, user_id: str, title: str) -> Course:
    order_index = course_repository.next_order_index(db, user_id=user_id)
    return course_repository.create(
        db, obj_in={"user_id": user_id, "title": title, "order_index": order_index}
    )


def list_courses_for_user(db: psycopg.Connection, *, user_id: str) -> list[Course]:
    return course_repository.list_for_user(db, user_id=user_id)


def get_course_for_user(db: psycopg.Connection, *, user_id: str, course_id: str) -> Course:
    course = course_repository.get_for_user(db, course_id=course_id, user_id=user_id)
    if not course:
        raise NotFoundError("Course not found.")
    return course


def rename_course(db: psycopg.Connection, *, user_id: str, course_id: str, title: str) -> Course:
    course = get_course_for_user(db, user_id=user_id, course_id=course_id)
    return course_repository.update(db, db_obj=course, obj_in={"title": title})


def delete_course(db: psycopg.Connection, *, user_id: str, course_id: str) -> None:
    course = get_course_for_user(db, user_id=user_id, course_id=course_id)
    # ON DELETE CASCADE on chapters.course_id handles the chapters (and,
    # through chapters, every note, highlight, and glossary entry
    # filed under them) -- one DELETE here is enough.
    course_repository.delete(db, id=course.id)


def reorder_courses(db: psycopg.Connection, *, user_id: str, ordered_ids: list[str]) -> list[Course]:
    """
    Re-numbers order_index to match the position of each id in
    `ordered_ids`. Every id is re-checked against get_course_for_user
    first so a student can never smuggle in someone else's course id and
    quietly reorder it too.
    """
    for index, course_id in enumerate(ordered_ids):
        course = get_course_for_user(db, user_id=user_id, course_id=course_id)
        course_repository.update(db, db_obj=course, obj_in={"order_index": index})
    return list_courses_for_user(db, user_id=user_id)


# --------------------------------------------------------------------------
# Chapters
# --------------------------------------------------------------------------

def create_chapter(db: psycopg.Connection, *, user_id: str, course_id: str, title: str) -> Chapter:
    # Ownership check on the parent course before creating anything inside it.
    get_course_for_user(db, user_id=user_id, course_id=course_id)
    order_index = chapter_repository.next_order_index(db, course_id=course_id)
    return chapter_repository.create(
        db,
        obj_in={"user_id": user_id, "course_id": course_id, "title": title, "order_index": order_index},
    )


def list_chapters_for_course(db: psycopg.Connection, *, user_id: str, course_id: str) -> list[Chapter]:
    get_course_for_user(db, user_id=user_id, course_id=course_id)
    return chapter_repository.list_for_course(db, course_id=course_id, user_id=user_id)


def get_chapter_for_user(db: psycopg.Connection, *, user_id: str, chapter_id: str) -> Chapter:
    chapter = chapter_repository.get_for_user(db, chapter_id=chapter_id, user_id=user_id)
    if not chapter:
        raise NotFoundError("Chapter not found.")
    return chapter


def rename_chapter(db: psycopg.Connection, *, user_id: str, chapter_id: str, title: str) -> Chapter:
    chapter = get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)
    return chapter_repository.update(db, db_obj=chapter, obj_in={"title": title})


def delete_chapter(db: psycopg.Connection, *, user_id: str, chapter_id: str) -> None:
    chapter = get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)
    # ON DELETE CASCADE handles notes, highlights, and glossary rows
    # filed under this chapter. study_guides.chapter_id uses ON DELETE SET
    # NULL instead (see schema.sql) -- a generated guide survives its
    # chapter being deleted, it just becomes unfiled again.
    chapter_repository.delete(db, id=chapter.id)


def reorder_chapters(
    db: psycopg.Connection, *, user_id: str, course_id: str, ordered_ids: list[str]
) -> list[Chapter]:
    get_course_for_user(db, user_id=user_id, course_id=course_id)
    for index, chapter_id in enumerate(ordered_ids):
        chapter = get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)
        chapter_repository.update(db, db_obj=chapter, obj_in={"order_index": index})
    return chapter_repository.list_for_course(db, course_id=course_id, user_id=user_id)


# --------------------------------------------------------------------------
# Chapter workspace -- everything filed under one chapter, one call
# --------------------------------------------------------------------------

def get_chapter_contents(db: psycopg.Connection, *, user_id: str, chapter_id: str) -> dict:
    """
    Used by the Chapter Workspace page: one call that returns the chapter
    itself plus every study guide and note filed inside it, instead of the
    frontend making three separate round trips on every page load.
    """
    chapter = get_chapter_for_user(db, user_id=user_id, chapter_id=chapter_id)
    guides = study_guide_repository.list_for_chapter(db, chapter_id=chapter_id, user_id=user_id)
    notes = note_repository.list_for_chapter(db, chapter_id=chapter_id, user_id=user_id)
    return {"chapter": chapter, "study_guides": guides, "notes": notes}
