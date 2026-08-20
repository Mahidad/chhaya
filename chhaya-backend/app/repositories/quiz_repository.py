"""Raw PostgreSQL queries for Module 3 Feature 7 – Quiz Generation."""

import uuid
from datetime import datetime

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.models.quiz import Quiz, QuizQuestion


# ── helpers ──────────────────────────────────────────────────────────────────

def _to_quiz(row: dict | None) -> Quiz | None:
    return Quiz(**row) if row else None


def _to_question(row: dict | None) -> QuizQuestion | None:
    return QuizQuestion(**row) if row else None


# ── quizzes ───────────────────────────────────────────────────────────────────

def create_quiz(
    db: psycopg.Connection,
    *,
    user_id: str,
    chapter_id: str,
    note_id: str | None,
    title: str,
    difficulty: str,
    num_questions: int,
    min_marks: int,
    max_marks: int,
    duration_minutes: int,
    attempt_number: int,
) -> Quiz:
    """Insert a new quiz row and return it."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO quizzes
              (id, user_id, chapter_id, note_id, title, difficulty,
               num_questions, min_marks, max_marks, duration_minutes, attempt_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                str(uuid.uuid4()),
                user_id, chapter_id, note_id, title, difficulty,
                num_questions, min_marks, max_marks, duration_minutes, attempt_number,
            ),
        )
        return _to_quiz(cur.fetchone())


def create_question(
    db: psycopg.Connection,
    *,
    quiz_id: str,
    question_text: str,
    marks: int,
    difficulty: str,
) -> QuizQuestion:
    """Insert one question row for a quiz."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO quiz_questions (id, quiz_id, question_text, marks, difficulty)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (str(uuid.uuid4()), quiz_id, question_text, marks, difficulty),
        )
        return _to_question(cur.fetchone())


def get_quiz_for_user(
    db: psycopg.Connection, *, quiz_id: str, user_id: str
) -> Quiz | None:
    """Fetch one quiz — returns None if it doesn't belong to this user."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM quizzes WHERE id = %s AND user_id = %s",
            (quiz_id, user_id),
        )
        return _to_quiz(cur.fetchone())


def list_quizzes_for_user(
    db: psycopg.Connection, *, user_id: str
) -> list[Quiz]:
    """Return all quizzes for one student, newest first."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM quizzes WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        return [Quiz(**row) for row in cur.fetchall()]


def list_questions(
    db: psycopg.Connection, *, quiz_id: str
) -> list[QuizQuestion]:
    """Return all questions for one quiz in insertion order."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM quiz_questions WHERE quiz_id = %s",
            (quiz_id,),
        )
        return [QuizQuestion(**row) for row in cur.fetchall()]


def count_attempts_for_chapter(
    db: psycopg.Connection, *, user_id: str, chapter_id: str
) -> int:
    """Count how many quizzes this user has generated for this chapter."""
    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM quizzes WHERE user_id = %s AND chapter_id = %s",
            (user_id, chapter_id),
        )
        return cur.fetchone()[0]


def count_attempts_for_note(
    db: psycopg.Connection, *, user_id: str, note_id: str
) -> int:
    """Count how many quizzes this user has generated from this specific note."""
    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM quizzes WHERE user_id = %s AND note_id = %s",
            (user_id, note_id),
        )
        return cur.fetchone()[0]


def start_quiz(
    db: psycopg.Connection,
    *,
    quiz_id: str,
    user_id: str,
    started_at: datetime,
    ends_at: datetime,
) -> Quiz | None:
    """Record the start timestamp and compute the deadline."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            UPDATE quizzes
               SET status = 'in_progress', started_at = %s, ends_at = %s
             WHERE id = %s AND user_id = %s AND status = 'not_started'
            RETURNING *
            """,
            (started_at, ends_at, quiz_id, user_id),
        )
        return _to_quiz(cur.fetchone())


def submit_quiz(
    db: psycopg.Connection,
    *,
    quiz_id: str,
    user_id: str,
    answers: list,
    status: str,
    submitted_at: datetime,
) -> Quiz | None:
    """Save answers and mark the quiz as submitted or auto_submitted."""
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            UPDATE quizzes
               SET status = %s, answers = %s, submitted_at = %s
             WHERE id = %s AND user_id = %s AND status = 'in_progress'
            RETURNING *
            """,
            (status, Jsonb(answers), submitted_at, quiz_id, user_id),
        )
        return _to_quiz(cur.fetchone())


def delete_quiz(
    db: psycopg.Connection, *, quiz_id: str, user_id: str
) -> bool:
    """Delete a quiz (cascade removes its questions too)."""
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM quizzes WHERE id = %s AND user_id = %s",
            (quiz_id, user_id),
        )
        return cur.rowcount > 0


def save_grading_result(
    db: psycopg.Connection,
    *,
    quiz_id: str,
    user_id: str,
    total_score: int,
    max_score: int,
    percentage: float,
    pass_status: str,
    graded_answers: list,
) -> Quiz | None:
    """Write the grading outcome back onto the quiz row."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            UPDATE quizzes
               SET total_score    = %s,
                   max_score      = %s,
                   percentage     = %s,
                   pass_status    = %s,
                   graded_answers = %s,
                   graded_at      = %s
             WHERE id = %s AND user_id = %s
            RETURNING *
            """,
            (
                total_score, max_score, percentage, pass_status,
                Jsonb(graded_answers), now,
                quiz_id, user_id,
            ),
        )
        return _to_quiz(cur.fetchone())

