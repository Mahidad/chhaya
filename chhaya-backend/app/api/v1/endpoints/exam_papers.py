from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.exam_paper import ExamPaperOut
from app.services import exam_paper_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/exam-papers", tags=["exam-papers"])


@router.post("", response_model=ExamPaperOut, status_code=status.HTTP_201_CREATED)
async def upload_exam_paper(
    title: str = Form(...),
    course: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    File uploads use `multipart/form-data`, not JSON -- that's why this
    endpoint takes `Form(...)` fields instead of a Pydantic body schema
    like every other POST endpoint in this app. FastAPI can't mix a JSON
    body and a file in the same request, so text fields that travel
    alongside a file become form fields too.
    """
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
def list_exam_papers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return exam_paper_service.list_papers_for_user(db, user_id=current_user.id)


@router.get("/{paper_id}", response_model=ExamPaperOut)
def get_exam_paper(
    paper_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        return exam_paper_service.get_paper_for_user(db, user_id=current_user.id, paper_id=paper_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
