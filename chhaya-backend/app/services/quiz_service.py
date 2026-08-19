"""Business logic for Module 3 Feature 7 – Quiz Generation.

This service sits between the API endpoint and the repositories.
It orchestrates:
  1. Fetching notes and validating content length
  2. Calling the generation service (Gemini)
  3. Calculating quiz duration
  4. Saving the quiz and questions to the DB
  5. Managing the quiz lifecycle (start, submit)
"""

from datetime import datetime, timedelta, timezone

import psycopg

from app.models.quiz import Quiz, QuizQuestion
from app.repositories import quiz_repository
from app.services import quiz_generation_service

# Minutes per question for each difficulty level
MINUTES_PER_QUESTION = {
    "easy": 2,
    "medium": 3,
    "hard": 5,
}

# Notes must have at least this many words to generate a quiz
MIN_WORD_COUNT = 100

# Notes are truncated to this many characters before sending to Gemini
MAX_CHAR_LIMIT = 15000


# ── helpers ───────────────────────────────────────────────────────────────────

def _fetch_notes_text(db: psycopg.Connection, *, chapter_id: str, user_id: str) -> str:
    """
    Fetch all typed notes for a chapter and join them into one block of text.
    Only 'text' type notes have text_content; image/pdf notes are skipped.
    """
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT text_content
              FROM notes
             WHERE chapter_id = %s AND user_id = %s AND note_type = 'text'
               AND text_content IS NOT NULL
             ORDER BY created_at ASC
            """,
            (chapter_id, user_id),
        )
        rows = cur.fetchall()

    # Join all note bodies with a blank line separator
    combined = "\n\n".join(row[0] for row in rows if row[0])
    return combined


def _calculate_duration(num_questions: int, difficulty: str) -> int:
    """Return total quiz duration in minutes."""
    minutes_per_q = MINUTES_PER_QUESTION.get(difficulty, 3)
    return num_questions * minutes_per_q


# ── main actions ──────────────────────────────────────────────────────────────

def generate_quiz(
    db: psycopg.Connection,
    *,
    user_id: str,
    chapter_id: str,
    num_questions: int,
    marks_per_question: int,
    difficulty: str,
) -> tuple[Quiz, list[QuizQuestion]]:
    """
    Full generation pipeline:
      1. Fetch notes text for the chapter
      2. Check word count (reject if too short)
      3. Truncate if too long
      4. Ask Gemini to generate questions
      5. Calculate duration
      6. Figure out attempt number
      7. Save quiz + questions to DB
      8. Return (quiz, questions)
    """
    # Step 1: fetch notes
    notes_text = _fetch_notes_text(db, chapter_id=chapter_id, user_id=user_id)

    # Step 2: validate minimum content
    word_count = len(notes_text.split())
    if word_count < MIN_WORD_COUNT:
        raise ValueError(
            f"Not enough notes content. Your notes for this chapter have only "
            f"{word_count} words. Please add more notes (minimum {MIN_WORD_COUNT} words) "
            "before generating a quiz."
        )

    # Step 3: truncate if too long
    if len(notes_text) > MAX_CHAR_LIMIT:
        notes_text = notes_text[:MAX_CHAR_LIMIT]

    # Step 4: generate questions via Gemini
    raw_questions = quiz_generation_service.generate_questions(
        notes_text=notes_text,
        num_questions=num_questions,
        marks_per_question=marks_per_question,
        difficulty=difficulty,
    )

    # Step 5: calculate duration
    duration_minutes = _calculate_duration(num_questions, difficulty)

    # Step 6: attempt number = how many quizzes exist for this chapter + 1
    existing_count = quiz_repository.count_attempts_for_chapter(
        db, user_id=user_id, chapter_id=chapter_id
    )
    attempt_number = existing_count + 1

    # Step 7: save quiz header row
    title = f"Quiz – {difficulty.capitalize()} ({num_questions}Q)"
    quiz = quiz_repository.create_quiz(
        db,
        user_id=user_id,
        chapter_id=chapter_id,
        title=title,
        difficulty=difficulty,
        num_questions=num_questions,
        marks_per_question=marks_per_question,
        duration_minutes=duration_minutes,
        attempt_number=attempt_number,
    )

    # Step 8: save each question row
    questions = []
    for q in raw_questions:
        question = quiz_repository.create_question(
            db,
            quiz_id=quiz.id,
            question_text=q["question_text"],
            marks=q["marks"],
            difficulty=q["difficulty"],
        )
        questions.append(question)

    return quiz, questions


def start_quiz(
    db: psycopg.Connection, *, user_id: str, quiz_id: str
) -> Quiz | None:
    """
    Record when the student started and compute the hard deadline (ends_at).
    The quiz must be in 'not_started' status — the DB UPDATE enforces this.
    """
    quiz = quiz_repository.get_quiz_for_user(db, quiz_id=quiz_id, user_id=user_id)
    if quiz is None:
        return None

    now = datetime.now(timezone.utc)
    ends_at = now + timedelta(minutes=quiz.duration_minutes)

    return quiz_repository.start_quiz(
        db,
        quiz_id=quiz_id,
        user_id=user_id,
        started_at=now,
        ends_at=ends_at,
    )


def submit_quiz(
    db: psycopg.Connection,
    *,
    user_id: str,
    quiz_id: str,
    answers: list,
) -> Quiz | None:
    """
    Accept a submission. Compare server time vs ends_at to decide:
      - submitted      (student clicked submit before time ran out)
      - auto_submitted (timer expired on the frontend and it called submit)
    The quiz must be 'in_progress' — the DB UPDATE enforces this.
    """
    quiz = quiz_repository.get_quiz_for_user(db, quiz_id=quiz_id, user_id=user_id)
    if quiz is None:
        return None

    now = datetime.now(timezone.utc)

    # Compare as UTC-aware timestamps
    ends_at = quiz.ends_at
    if ends_at is not None and ends_at.tzinfo is None:
        # DB returned a naive datetime — treat it as UTC
        ends_at = ends_at.replace(tzinfo=timezone.utc)

    if ends_at is not None and now >= ends_at:
        final_status = "auto_submitted"
    else:
        final_status = "submitted"

    return quiz_repository.submit_quiz(
        db,
        quiz_id=quiz_id,
        user_id=user_id,
        answers=answers,
        status=final_status,
        submitted_at=now,
    )


def get_quiz_detail(
    db: psycopg.Connection, *, user_id: str, quiz_id: str
) -> tuple[Quiz, list[QuizQuestion]] | None:
    """Return the quiz and its questions, or None if not found."""
    quiz = quiz_repository.get_quiz_for_user(db, quiz_id=quiz_id, user_id=user_id)
    if quiz is None:
        return None
    questions = quiz_repository.list_questions(db, quiz_id=quiz_id)
    return quiz, questions


def list_quizzes(
    db: psycopg.Connection, *, user_id: str
) -> list[Quiz]:
    """Return all quizzes for this student."""
    return quiz_repository.list_quizzes_for_user(db, user_id=user_id)


def delete_quiz(
    db: psycopg.Connection, *, user_id: str, quiz_id: str
) -> bool:
    """Delete a quiz and all its questions."""
    return quiz_repository.delete_quiz(db, quiz_id=quiz_id, user_id=user_id)
