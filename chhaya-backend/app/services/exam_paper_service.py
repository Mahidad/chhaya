
import os         #lets Python interact with the operating system.
import uuid

import psycopg

from app.models.exam_paper import ExamPaper, ExamPaperStatus
from app.repositories.exam_paper_repository import exam_paper_repository
from app.utils.exceptions import NotFoundError
from app.utils.ocr import extract_text_from_image

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "exam_papers"
)


def _save_upload(file_bytes: bytes, original_filename: str) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(original_filename)[1] or ".bin"
    stored_name = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, stored_name)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


def create_and_process(
    db: psycopg.Connection,
    *,
    user_id: str,
    title: str,
    course: str | None,
    file_bytes: bytes,
    filename: str,
) -> ExamPaper:      # return kore ExamPaper object
    file_path = _save_upload(file_bytes, filename)

    paper = exam_paper_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "title": title,
            "course": course,
            "file_path": file_path,
            "status": ExamPaperStatus.PENDING,
        },
    )

    try:
        paper = exam_paper_repository.update(
            db, db_obj=paper, obj_in={"status": ExamPaperStatus.PROCESSING}
        )
        text = extract_text_from_image(file_path)
        paper = exam_paper_repository.update(
            db,
            db_obj=paper,
            obj_in={"extracted_text": text, "status": ExamPaperStatus.READY},
        )
    except Exception as exc:  # noqa: BLE001
        paper = exam_paper_repository.update(
            db,
            db_obj=paper,
            obj_in={"status": ExamPaperStatus.FAILED, "error_message": str(exc)},
        )

    return paper


def list_papers_for_user(
    db: psycopg.Connection, *, user_id: str
) -> list[ExamPaper]:
    return exam_paper_repository.list_for_user(db, user_id=user_id)


def get_paper_for_user(
    db: psycopg.Connection, *, user_id: str, paper_id: str  #The * means everything after it must be passed as keyword arguments.
) -> ExamPaper:
    paper = exam_paper_repository.get_for_user(
        db, paper_id=paper_id, user_id=user_id
    )
    if not paper:
        raise NotFoundError("Exam paper not found.")
    return paper


def delete_paper_for_user(
    db: psycopg.Connection, *, user_id: str, paper_id: str
) -> None:
    paper = get_paper_for_user(db, user_id=user_id, paper_id=paper_id)
    if paper.file_path and os.path.exists(paper.file_path):
        try:
            os.remove(paper.file_path)
        except OSError:
            pass
    exam_paper_repository.delete(db, id=paper.id)
