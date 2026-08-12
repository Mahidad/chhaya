import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.code_conversion import (
    CodeConversionOut,
    CodeConversionSolveCreate,
    CodeConversionTranslateCreate,
)
from app.services import code_converter_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/code-conversions", tags=["code-conversions"])


@router.post("/translate", response_model=CodeConversionOut, status_code=status.HTTP_201_CREATED)
def translate(
    payload: CodeConversionTranslateCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Runs synchronously, same trade-off as every other Gemini-backed
    endpoint in this app (see reference_source_service.py's docstring) --
    fine for a single conversion, would need a background task if this
    ever needs to handle very large files.
    """
    try:
        return code_converter_service.create_and_translate(db, user_id=current_user.id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/solve", response_model=CodeConversionOut, status_code=status.HTTP_201_CREATED)
def solve(
    payload: CodeConversionSolveCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return code_converter_service.create_and_solve(db, user_id=current_user.id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=list[CodeConversionOut])
def list_conversions(
    db: psycopg.Connection = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return code_converter_service.list_conversions_for_user(db, user_id=current_user.id)


@router.get("/{conversion_id}", response_model=CodeConversionOut)
def get_conversion(
    conversion_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return code_converter_service.get_conversion_for_user(
            db, user_id=current_user.id, conversion_id=conversion_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
