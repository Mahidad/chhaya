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

from app.models.note import Note, NoteType
from app.models.quiz import Quiz, QuizQuestion
from app.repositories import quiz_repository
from app.repositories.note_repository import note_repository
from app.services import quiz_generation_service

import math

# Base minutes per question by difficulty (used in duration formula)
BASE_MINUTES = {
    "easy": 2,
    "medium": 3,
    "hard": 5,
}

# Notes must have at least this many words to generate a quiz
MIN_WORD_COUNT = 100

# Notes are truncated to this many characters before sending to Gemini
MAX_CHAR_LIMIT = 15000


# ── helpers ───────────────────────────────────────────────────────────────────

def _fetch_note(db: psycopg.Connection, *, note_id: str, user_id: str) -> Note:
    """
    Fetch a single note by ID, verifying it belongs to this user.
    Raises ValueError if not found.
    """
    note = note_repository.get_for_user(db, note_id=note_id, user_id=user_id)
    if note is None:
        raise ValueError(
            "Note not found. It may have been deleted or doesn't belong to you."
        )
    return note


def _calculate_duration(questions: list[dict]) -> int:
    """
    Return total quiz duration in minutes.

    Formula per question:
      base_time = BASE_MINUTES[difficulty]   (2 / 3 / 5)
      time_for_question = base_time + (marks * 0.5)   # +30 sec per mark

    Total is summed across all questions, then rounded up to the nearest minute.
    """
    total_seconds = 0.0
    for q in questions:
        difficulty = q.get("difficulty", "medium").lower()
        marks = q.get("marks", 1)
        base = BASE_MINUTES.get(difficulty, 3)
        total_seconds += (base + marks * 0.5) * 60
    return math.ceil(total_seconds / 60)


# ── main actions ──────────────────────────────────────────────────────────────

def generate_quiz(
    db: psycopg.Connection,
    *,
    user_id: str,
    note_id: str,
    num_questions: int,
    min_marks: int,
    max_marks: int,
    difficulty: str,
) -> tuple[Quiz, list[QuizQuestion]]:
    """
    Full generation pipeline:
      1. Fetch the selected note and verify ownership
      2. Branch on note_type:
           - 'text'       → send text_content to Gemini (existing flow)
           - 'pdf'/'image' → send the file to Gemini as a multimodal part
      3. Validate content (word-count for text; file existence for PDF/image)
      4. Ask Gemini to generate questions
      5. Calculate duration from per-question marks + difficulty
      6. Derive chapter_id from the note itself
      7. Count attempts per note (not per chapter)
      8. Save quiz + questions to DB
      9. Return (quiz, questions)
    """
    # Step 1: fetch the note
    note = _fetch_note(db, note_id=note_id, user_id=user_id)
    chapter_id = note.chapter_id

    # Step 2 & 3: branch on note type and validate
    if note.note_type == NoteType.TEXT:
        notes_text = note.text_content or ""
        word_count = len(notes_text.split())
        if word_count < MIN_WORD_COUNT:
            raise ValueError(
                f"Not enough notes content. This note has only {word_count} words. "
                f"Please add more text (minimum {MIN_WORD_COUNT} words) before generating a quiz."
            )
        # Truncate if too long
        if len(notes_text) > MAX_CHAR_LIMIT:
            notes_text = notes_text[:MAX_CHAR_LIMIT]

        # Step 4: generate via text path
        raw_questions = quiz_generation_service.generate_questions(
            notes_text=notes_text,
            num_questions=num_questions,
            min_marks=min_marks,
            max_marks=max_marks,
            difficulty=difficulty,
        )
    else:
        # PDF or image note — validate file is readable before calling Gemini
        if not note.file_path:
            raise ValueError(
                "This note has no file attached. Please re-upload the note and try again."
            )

        # Step 4: generate via multimodal path
        raw_questions = quiz_generation_service.generate_questions_from_file(
            file_path=note.file_path,
            num_questions=num_questions,
            min_marks=min_marks,
            max_marks=max_marks,
            difficulty=difficulty,
        )

    # Step 5: calculate duration from per-question difficulty + marks
    duration_minutes = _calculate_duration(raw_questions)

    # Step 6 & 7: derive chapter, count per-note attempts
    existing_count = quiz_repository.count_attempts_for_note(
        db, user_id=user_id, note_id=note_id
    )
    attempt_number = existing_count + 1

    # Step 8: save quiz header row (chapter_id kept for list-page grouping)
    note_type_label = "Text" if note.note_type == NoteType.TEXT else note.note_type.upper()
    title = f"Quiz – {difficulty.capitalize()} ({num_questions}Q, {min_marks}–{max_marks}M) [{note_type_label}]"
    quiz = quiz_repository.create_quiz(
        db,
        user_id=user_id,
        chapter_id=chapter_id,
        note_id=note_id,
        title=title,
        difficulty=difficulty,
        num_questions=num_questions,
        min_marks=min_marks,
        max_marks=max_marks,
        duration_minutes=duration_minutes,
        attempt_number=attempt_number,
    )

    # Step 9: save each question row
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
