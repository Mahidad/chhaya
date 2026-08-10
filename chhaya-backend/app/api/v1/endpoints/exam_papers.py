import psycopg
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.exam_paper import ExamPaperOut
from app.services import exam_paper_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/exam-papers", tags=["exam-papers"])


@router.post("", response_model=ExamPaperOut, status_code=status.HTTP_201_CREATED) # return korbe ExamPaperOut schema model er ekta object ebong 201 status code
async def upload_exam_paper(
    title: str = Form(...),       # required field
    course: str | None = Form(None),      # optional field
    file: UploadFile = File(...),     
    db: psycopg.Connection = Depends(get_db),   # database connection
    current_user: User = Depends(get_current_user),   # current user
):

    file_bytes = await file.read()
    return exam_paper_service.create_and_process(
        db,
        user_id=current_user.id,
        title=title,
        course=course,
        file_bytes=file_bytes,
        filename=file.filename or "upload",
    )


@router.get("", response_model=list[ExamPaperOut])
def list_exam_papers(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return exam_paper_service.list_papers_for_user(db, user_id=current_user.id)


@router.get("/{paper_id}", response_model=ExamPaperOut)
def get_exam_paper(
    paper_id: str,
    db: psycopg.Connection = Depends(get_db),  #Before calling this function, create a database connection // equivalent to db = get_db() when the function runs
    current_user: User = Depends(get_current_user),
):
    try:
        return exam_paper_service.get_paper_for_user(
            db, user_id=current_user.id, paper_id=paper_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam_paper(
    paper_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        exam_paper_service.delete_paper_for_user(
            db, user_id=current_user.id, paper_id=paper_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{paper_id}/file")
def get_exam_paper_file(
    paper_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import os
    from fastapi.responses import FileResponse

    try:
        paper = exam_paper_service.get_paper_for_user(
            db, user_id=current_user.id, paper_id=paper_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not paper.file_path or not os.path.exists(paper.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk."
        )

    ext = os.path.splitext(paper.file_path)[1].lower()
    media_type = "application/pdf" if ext == ".pdf" else f"image/{ext.lstrip('.') or 'png'}"
    return FileResponse(paper.file_path, media_type=media_type)
