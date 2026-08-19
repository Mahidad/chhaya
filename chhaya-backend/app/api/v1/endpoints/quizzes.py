"""Module 3 Features 7 & 8 endpoints – Quiz Generation and Evaluation."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.quiz import (
    GradedAnswerOut,
    QuizDetailOut,
    QuizGenerateIn,
    QuizOut,
    QuizQuestionOut,
    QuizResultOut,
    QuizStartOut,
    QuizSubmitIn,
    QuizSubmitOut,
)
from app.services import quiz_service, quiz_grading_service
from app.repositories import quiz_repository
from app.utils.exceptions import ExternalServiceError

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.post("/generate", response_model=QuizDetailOut, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    payload: QuizGenerateIn,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a quiz from the student's typed notes for a chapter.
    Returns the quiz header plus all generated questions.
    """
    try:
        quiz, questions = quiz_service.generate_quiz(
            db,
            user_id=current_user.id,
            chapter_id=payload.chapter_id,
            num_questions=payload.num_questions,
            marks_per_question=payload.marks_per_question,
            difficulty=payload.difficulty,
        )
    except ValueError as exc:
        # Raised when notes are too short
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return QuizDetailOut(
        id=quiz.id,
        chapter_id=quiz.chapter_id,
        title=quiz.title,
        difficulty=quiz.difficulty,
        num_questions=quiz.num_questions,
        marks_per_question=quiz.marks_per_question,
        duration_minutes=quiz.duration_minutes,
        attempt_number=quiz.attempt_number,
        status=quiz.status,
        ends_at=quiz.ends_at,
        submitted_at=quiz.submitted_at,
        created_at=quiz.created_at,
        questions=[
            QuizQuestionOut(
                id=q.id,
                question_text=q.question_text,
                marks=q.marks,
                difficulty=q.difficulty,
            )
            for q in questions
        ],
    )


@router.get("", response_model=list[QuizOut])
def list_quizzes(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all quizzes for the current student, newest first."""
    quizzes = quiz_service.list_quizzes(db, user_id=current_user.id)
    return [
        QuizOut(
            id=q.id,
            chapter_id=q.chapter_id,
            title=q.title,
            difficulty=q.difficulty,
            num_questions=q.num_questions,
            marks_per_question=q.marks_per_question,
            duration_minutes=q.duration_minutes,
            attempt_number=q.attempt_number,
            status=q.status,
            ends_at=q.ends_at,
            submitted_at=q.submitted_at,
            created_at=q.created_at,
        )
        for q in quizzes
    ]


@router.get("/{quiz_id}", response_model=QuizDetailOut)
def get_quiz(
    quiz_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return one quiz with all its questions."""
    result = quiz_service.get_quiz_detail(db, user_id=current_user.id, quiz_id=quiz_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

    quiz, questions = result
    return QuizDetailOut(
        id=quiz.id,
        chapter_id=quiz.chapter_id,
        title=quiz.title,
        difficulty=quiz.difficulty,
        num_questions=quiz.num_questions,
        marks_per_question=quiz.marks_per_question,
        duration_minutes=quiz.duration_minutes,
        attempt_number=quiz.attempt_number,
        status=quiz.status,
        ends_at=quiz.ends_at,
        submitted_at=quiz.submitted_at,
        created_at=quiz.created_at,
        questions=[
            QuizQuestionOut(
                id=q.id,
                question_text=q.question_text,
                marks=q.marks,
                difficulty=q.difficulty,
            )
            for q in questions
        ],
    )


@router.post("/{quiz_id}/start", response_model=QuizStartOut)
def start_quiz(
    quiz_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark the quiz as started and lock in the deadline (ends_at).
    The frontend uses ends_at to drive the countdown timer.
    Can only be called when status is 'not_started'.
    """
    quiz = quiz_service.start_quiz(db, user_id=current_user.id, quiz_id=quiz_id)
    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or already started.",
        )
    return QuizStartOut(
        id=quiz.id,
        status=quiz.status,
        started_at=quiz.started_at,
        ends_at=quiz.ends_at,
    )


@router.post("/{quiz_id}/submit", response_model=QuizSubmitOut)
def submit_quiz(
    quiz_id: str,
    payload: QuizSubmitIn,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit answers for a quiz in progress.
    Backend checks server time vs ends_at to decide status:
      'submitted' (on time) or 'auto_submitted' (time expired).
    Can only be called when status is 'in_progress'.
    """
    answers_data = [
        {"question_id": a.question_id, "answer_text": a.answer_text}
        for a in payload.answers
    ]
    quiz = quiz_service.submit_quiz(
        db,
        user_id=current_user.id,
        quiz_id=quiz_id,
        answers=answers_data,
    )
    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or not in progress.",
        )
    return QuizSubmitOut(
        id=quiz.id,
        status=quiz.status,
        submitted_at=quiz.submitted_at,
    )


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a quiz and all its questions."""
    removed = quiz_service.delete_quiz(db, user_id=current_user.id, quiz_id=quiz_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")


# ── Feature 8 endpoints ───────────────────────────────────────────────────

@router.post("/{quiz_id}/grade", response_model=QuizResultOut)
def grade_quiz(
    quiz_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Grade a submitted quiz using Gemini.

    Fetches the quiz's stored answers and questions, calls Gemini once per
    question (with one retry on parse failure), calculates the official
    score using backend arithmetic, classifies the result into a status
    (good_job / required_retake / need_urgent_retake), and saves everything
    back to the quiz row.
    """
    # 1. Load the quiz
    quiz = quiz_repository.get_quiz_for_user(db, quiz_id=quiz_id, user_id=current_user.id)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

    # 2. Must be submitted before it can be graded
    if quiz.status not in ("submitted", "auto_submitted"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quiz must be submitted before it can be graded.",
        )

    # 3. Load the stored answers and questions
    stored_answers = quiz.answers or []
    questions = quiz_repository.list_questions(db, quiz_id=quiz_id)

    # 4. Call the grading service
    try:
        grading = quiz_grading_service.grade_quiz(
            questions=questions,
            answers=stored_answers,
        )
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    # 5. Save the result back to the DB
    updated_quiz = quiz_repository.save_grading_result(
        db,
        quiz_id=quiz_id,
        user_id=current_user.id,
        total_score=grading["total_score"],
        max_score=grading["max_score"],
        percentage=grading["percentage"],
        pass_status=grading["pass_status"],
        graded_answers=grading["graded_answers"],
    )

    # 6. Return full result
    return QuizResultOut(
        id=updated_quiz.id,
        chapter_id=updated_quiz.chapter_id,
        title=updated_quiz.title,
        difficulty=updated_quiz.difficulty,
        attempt_number=updated_quiz.attempt_number,
        num_questions=updated_quiz.num_questions,
        total_score=updated_quiz.total_score,
        max_score=updated_quiz.max_score,
        percentage=updated_quiz.percentage,
        pass_status=updated_quiz.pass_status,
        graded_at=updated_quiz.graded_at,
        graded_answers=[
            GradedAnswerOut(**ga) for ga in updated_quiz.graded_answers
        ],
    )


@router.get("/{quiz_id}/results", response_model=QuizResultOut)
def get_quiz_results(
    quiz_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the graded results for one quiz. Quiz must already be graded."""
    quiz = quiz_repository.get_quiz_for_user(db, quiz_id=quiz_id, user_id=current_user.id)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

    if quiz.graded_at is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This quiz has not been graded yet.",
        )

    return QuizResultOut(
        id=quiz.id,
        chapter_id=quiz.chapter_id,
        title=quiz.title,
        difficulty=quiz.difficulty,
        attempt_number=quiz.attempt_number,
        num_questions=quiz.num_questions,
        total_score=quiz.total_score,
        max_score=quiz.max_score,
        percentage=quiz.percentage,
        pass_status=quiz.pass_status,
        graded_at=quiz.graded_at,
        graded_answers=[
            GradedAnswerOut(**ga) for ga in (quiz.graded_answers or [])
        ],
    )


@router.post("/{quiz_id}/retry", response_model=QuizDetailOut, status_code=status.HTTP_201_CREATED)
def retry_quiz(
    quiz_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new quiz attempt for the same chapter and settings.

    Reads chapter_id + settings from the original quiz, then calls
    the same generation flow as Feature 7. The new quiz gets
    attempt_number = existing_count + 1. All previous attempts are
    kept unchanged in the DB so history stays accurate.
    """
    # Load the original quiz to copy its settings
    original = quiz_repository.get_quiz_for_user(
        db, quiz_id=quiz_id, user_id=current_user.id
    )
    if original is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

    try:
        quiz, questions = quiz_service.generate_quiz(
            db,
            user_id=current_user.id,
            chapter_id=original.chapter_id,
            num_questions=original.num_questions,
            marks_per_question=original.marks_per_question,
            difficulty=original.difficulty,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return QuizDetailOut(
        id=quiz.id,
        chapter_id=quiz.chapter_id,
        title=quiz.title,
        difficulty=quiz.difficulty,
        num_questions=quiz.num_questions,
        marks_per_question=quiz.marks_per_question,
        duration_minutes=quiz.duration_minutes,
        attempt_number=quiz.attempt_number,
        status=quiz.status,
        ends_at=quiz.ends_at,
        submitted_at=quiz.submitted_at,
        created_at=quiz.created_at,
        questions=[
            QuizQuestionOut(
                id=q.id,
                question_text=q.question_text,
                marks=q.marks,
                difficulty=q.difficulty,
            )
            for q in questions
        ],
    )
