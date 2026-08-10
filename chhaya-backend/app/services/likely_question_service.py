"""Orchestration for analysing OCR'd past papers into likely questions."""

import psycopg

from app.models.likely_question import LikelyQuestionSet, LikelyQuestionStatus
from app.repositories.exam_paper_repository import exam_paper_repository
from app.repositories.likely_question_repository import likely_question_repository
from app.schemas.likely_question import LikelyQuestionCreate
from app.services.likely_question_generation_service import analyze_and_predict
from app.utils.exceptions import NotFoundError


def create_and_generate(
    db: psycopg.Connection, *, user_id: str, payload: LikelyQuestionCreate
) -> LikelyQuestionSet:
    selected_papers = []
    for paper_id in dict.fromkeys(payload.exam_paper_ids):
        paper = exam_paper_repository.get_for_user(db, paper_id=paper_id, user_id=user_id)
        if not paper:
            raise NotFoundError("One of the selected exam papers was not found.")
        if paper.status != "ready" or not (paper.extracted_text or "").strip():
            raise ValueError(f'"{paper.title}" is not ready for analysis yet.')
        selected_papers.append(paper)

    question_set = likely_question_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "title": payload.title.strip(),
            "course": payload.course.strip() if payload.course else None,
            "status": LikelyQuestionStatus.PENDING,
            "source_paper_count": len(selected_papers),
            "source_paper_ids": {"ids": [paper.id for paper in selected_papers]},
        },
    )

    try:
        question_set = likely_question_repository.update(
            db, db_obj=question_set, obj_in={"status": LikelyQuestionStatus.ANALYZING}
        )
        result = analyze_and_predict(
            papers=[{"title": paper.title, "extracted_text": paper.extracted_text} for paper in selected_papers],
            question_count=payload.question_count,
        )
        question_set = likely_question_repository.update(
            db,
            db_obj=question_set,
            obj_in={
                "analysis": result["analysis"],
                "predicted_questions": result["predicted_questions"],
                "status": LikelyQuestionStatus.READY,
            },
        )
    except Exception as exc:  # noqa: BLE001
        question_set = likely_question_repository.update(
            db,
            db_obj=question_set,
            obj_in={"status": LikelyQuestionStatus.FAILED, "error_message": str(exc)},
        )
    return question_set


def list_sets_for_user(db: psycopg.Connection, *, user_id: str) -> list[LikelyQuestionSet]:
    return likely_question_repository.list_for_user(db, user_id=user_id)


def get_set_for_user(
    db: psycopg.Connection, *, user_id: str, set_id: str
) -> LikelyQuestionSet:
    question_set = likely_question_repository.get_for_user(db, set_id=set_id, user_id=user_id)
    if not question_set:
        raise NotFoundError("Likely-question set not found.")
    return question_set


def delete_set_for_user(db: psycopg.Connection, *, user_id: str, set_id: str) -> None:
    question_set = get_set_for_user(db, user_id=user_id, set_id=set_id)
    likely_question_repository.delete(db, id=question_set.id)
