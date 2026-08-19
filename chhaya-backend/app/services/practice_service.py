"""
Orchestration for Code Studio's Practice tab: suggest problems from a
folder's saved work, start a timed attempt, submit and judge it.

THE TIMER IS SERVER-SIDE. `started_at` is set by the database when the
attempt row is created, and `seconds_taken` is computed here on submit
from the real elapsed wall-clock time -- not sent up by the frontend.
A student refreshing the page, closing the tab, or editing a JS counter
can't change the recorded time, which matters because that number feeds
the dashboard's averages and pseudo-ranking.
"""

from datetime import datetime, timezone

import psycopg

from app.models.practice_attempt import AttemptStatus
from app.repositories.code_conversion_repository import code_conversion_repository
from app.repositories.code_visualization_repository import code_visualization_repository
from app.repositories.code_workspace_folder_repository import code_workspace_folder_repository
from app.repositories.practice_attempt_repository import practice_attempt_repository
from app.repositories.practice_problem_repository import practice_problem_repository
from app.schemas.practice import StartAttemptRequest, SubmitAttemptRequest, SuggestProblemsRequest
from app.services import practice_ai_service
from app.utils.exceptions import NotFoundError

# How many candidate problems from the bank get shown to Gemini for
# matching. Capped because the whole bank could be thousands of rows --
# far more than fits in a prompt, and more than the model needs to make a
# sensible pick.
MATCH_CANDIDATE_POOL = 120


def _folder_work_summary(db: psycopg.Connection, *, user_id: str, folder_id: str) -> str:
    """
    Builds the "here's what this student has been working on" text that
    problem matching reasons over -- the code they translated/solved plus
    anything they traced, concatenated. Raises if the folder isn't theirs.
    """
    folder = code_workspace_folder_repository.get_for_user(db, folder_id=folder_id, user_id=user_id)
    if not folder:
        raise NotFoundError("Folder not found.")

    conversions = [
        c for c in code_conversion_repository.list_for_user(db, user_id=user_id)
        if c.folder_id == folder_id
    ]
    visualizations = [
        v for v in code_visualization_repository.list_for_user(db, user_id=user_id)
        if v.folder_id == folder_id
    ]

    parts = []
    for c in conversions:
        if c.problem_statement:
            parts.append(f"Problem solved: {c.problem_statement}")
        if c.output_code:
            parts.append(c.output_code)
        elif c.source_code:
            parts.append(c.source_code)
    for v in visualizations:
        parts.append(v.source_code)

    if not parts:
        raise NotFoundError("That folder has no saved work yet to base suggestions on.")

    return "\n\n---\n\n".join(parts)


def suggest_problems(db: psycopg.Connection, *, user_id: str, payload: SuggestProblemsRequest):
    work_summary = _folder_work_summary(db, user_id=user_id, folder_id=payload.folder_id)

    # Already-solved problems are excluded in SQL, so this pool is entirely
    # made of problems the student has not solved correctly yet.
    candidates = practice_problem_repository.list_unsolved_for_user(
        db, user_id=user_id, difficulty=payload.difficulty, limit=MATCH_CANDIDATE_POOL
    )
    if not candidates:
        if practice_problem_repository.list_by_difficulty(db, difficulty=payload.difficulty, limit=1):
            raise NotFoundError(
                f"You have already solved every {payload.difficulty} problem in the bank. "
                "Try a different difficulty."
            )
        raise NotFoundError(
            f"No {payload.difficulty} problems in the bank yet -- run scripts/import_practice_problems.py first."
        )

    picks = practice_ai_service.match_problems(
        work_summary=work_summary, problems=candidates, limit=payload.limit
    )

    # Only trust picks that came from the pool we offered. Gemini returns
    # slugs as free text, so it can echo back one that was never in the
    # candidate list -- a solved problem it knows from training, or a
    # plausible-looking slug that doesn't exist. Anything not in the pool is
    # dropped rather than looked up, which is also what keeps solved
    # problems from reappearing here.
    allowed = {c.title_slug for c in candidates}
    slugs = [p["title_slug"] for p in picks if p.get("title_slug") in allowed][: payload.limit]
    problems = practice_problem_repository.get_many_by_slugs(db, slugs=slugs)

    # Preserve Gemini's ordering (get_many_by_slugs returns DB order) and
    # attach each pick's reason.
    reason_by_slug = {p["title_slug"]: p.get("reason") for p in picks}
    by_slug = {p.title_slug: p for p in problems}
    ordered = []
    for slug in slugs:
        if slug in by_slug:
            problem = by_slug[slug]
            ordered.append({"problem": problem, "reason": reason_by_slug.get(slug)})
    return ordered


def start_attempt(db: psycopg.Connection, *, user_id: str, payload: StartAttemptRequest):
    problem = practice_problem_repository.get(db, payload.problem_id)
    if not problem:
        raise NotFoundError("Problem not found.")

    return practice_attempt_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "problem_id": problem.id,
            "folder_id": payload.folder_id,
            "status": AttemptStatus.IN_PROGRESS,
        },
    )


def submit_attempt(
    db: psycopg.Connection, *, user_id: str, attempt_id: str, payload: SubmitAttemptRequest
):
    attempt = practice_attempt_repository.get_for_user(db, attempt_id=attempt_id, user_id=user_id)
    if not attempt:
        raise NotFoundError("Attempt not found.")

    problem = practice_problem_repository.get(db, attempt.problem_id)
    if not problem:
        raise NotFoundError("Problem not found.")

    submitted_at = datetime.now(timezone.utc)
    seconds_taken = int((submitted_at - attempt.started_at).total_seconds())

    try:
        verdict = practice_ai_service.judge_submission(
            problem_description=problem.description,
            submitted_code=payload.submitted_code,
            language=payload.language,
        )
    except Exception as exc:  # noqa: BLE001
        # A judging failure must not lose the student's submission or their
        # elapsed time -- record everything, leave is_correct NULL, and say so.
        return practice_attempt_repository.update(
            db,
            db_obj=attempt,
            obj_in={
                "status": AttemptStatus.SUBMITTED,
                "submitted_code": payload.submitted_code,
                "language": payload.language,
                "seconds_taken": seconds_taken,
                "submitted_at": submitted_at,
                "feedback": f"Your solution was saved, but automatic review failed: {exc}",
            },
        )

    return practice_attempt_repository.update(
        db,
        db_obj=attempt,
        obj_in={
            "status": AttemptStatus.SUBMITTED,
            "submitted_code": payload.submitted_code,
            "language": payload.language,
            "seconds_taken": seconds_taken,
            "submitted_at": submitted_at,
            "is_correct": verdict.get("is_correct"),
            "feedback": verdict.get("feedback"),
            "time_complexity": verdict.get("time_complexity"),
            "space_complexity": verdict.get("space_complexity"),
        },
    )


def list_attempts_for_user(db: psycopg.Connection, *, user_id: str):
    return practice_attempt_repository.list_for_user(db, user_id=user_id)


def get_attempt_for_user(db: psycopg.Connection, *, user_id: str, attempt_id: str):
    attempt = practice_attempt_repository.get_for_user(db, attempt_id=attempt_id, user_id=user_id)
    if not attempt:
        raise NotFoundError("Attempt not found.")
    return attempt


def list_problems(db: psycopg.Connection, *, difficulty: str | None = None):
    if difficulty:
        return practice_problem_repository.list_by_difficulty(db, difficulty=difficulty)
    return practice_problem_repository.get_multi(db, limit=200)
