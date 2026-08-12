"""Raw PostgreSQL queries for Module 2 spaced-repetition review schedules."""

import uuid
from datetime import date

import psycopg
from psycopg.rows import dict_row

from app.models.review_schedule import ReviewSchedule


def _to_schedule(row: dict | None) -> ReviewSchedule | None:
    return ReviewSchedule(**row) if row else None


def create_for_study_guide(
    db: psycopg.Connection, *, user_id: str, study_guide_id: str
) -> ReviewSchedule | None:
    """Create one review entry from an owned study guide, unless it already exists."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO review_schedules (id, user_id, study_guide_id, topic)
            SELECT %s, sg.user_id, sg.id, sg.topic
              FROM study_guides AS sg
             WHERE sg.id = %s AND sg.user_id = %s
            ON CONFLICT (user_id, study_guide_id) DO NOTHING
            RETURNING *
            """,
            (str(uuid.uuid4()), study_guide_id, user_id),
        )
        return _to_schedule(cur.fetchone())


def list_for_user(
    db: psycopg.Connection, *, user_id: str, status: str
) -> list[ReviewSchedule]:
    """Return due, upcoming, or all review entries for one student."""
    filters = {
        "due": "next_review_date <= CURRENT_DATE",
        "upcoming": "next_review_date > CURRENT_DATE",
        "all": "TRUE",
    }
    condition = filters[status]

    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT *
              FROM review_schedules
             WHERE user_id = %s AND {condition}
             ORDER BY next_review_date ASC, created_at ASC
            """,
            (user_id,),
        )
        return [ReviewSchedule(**row) for row in cur.fetchall()]


def get_for_user(
    db: psycopg.Connection, *, review_id: str, user_id: str
) -> ReviewSchedule | None:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM review_schedules WHERE id = %s AND user_id = %s",
            (review_id, user_id),
        )
        return _to_schedule(cur.fetchone())


def update_after_rating(
    db: psycopg.Connection,
    *,
    review_id: str,
    user_id: str,
    ease_factor: float,
    interval_days: int,
    review_count: int,
    next_review_date: date,
) -> ReviewSchedule | None:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            UPDATE review_schedules
               SET ease_factor = %s,
                   interval_days = %s,
                   review_count = %s,
                   next_review_date = %s,
                   last_reviewed_on = CURRENT_DATE,
                   updated_at = NOW()
             WHERE id = %s AND user_id = %s
            RETURNING *
            """,
            (
                ease_factor,
                interval_days,
                review_count,
                next_review_date,
                review_id,
                user_id,
            ),
        )
        return _to_schedule(cur.fetchone())


def delete_for_user(
    db: psycopg.Connection, *, review_id: str, user_id: str
) -> bool:
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM review_schedules WHERE id = %s AND user_id = %s",
            (review_id, user_id),
        )
        return cur.rowcount > 0


def list_due_for_reminder(
    db: psycopg.Connection, *, user_id: str
) -> list[dict]:
    """Return due reviews not already emailed today, together with user email."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT rs.id, rs.topic, rs.next_review_date, u.email, u.full_name
              FROM review_schedules AS rs
              JOIN users AS u ON u.id = rs.user_id
             WHERE rs.user_id = %s
               AND rs.next_review_date <= CURRENT_DATE
               AND (rs.last_reminded_on IS NULL OR rs.last_reminded_on < CURRENT_DATE)
             ORDER BY rs.next_review_date ASC
            """,
            (user_id,),
        )
        return cur.fetchall()


def mark_reminded_today(db: psycopg.Connection, *, review_id: str, user_id: str) -> None:
    with db.cursor() as cur:
        cur.execute(
            """
            UPDATE review_schedules
               SET last_reminded_on = CURRENT_DATE, updated_at = NOW()
             WHERE id = %s AND user_id = %s
            """,
            (review_id, user_id),
        )
