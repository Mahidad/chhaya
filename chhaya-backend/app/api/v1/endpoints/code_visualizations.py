import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.code_visualization import (
    CodeVisualizationCreate,
    CodeVisualizationOut,
    CodeVisualizationUpdate,
)
from app.services import code_visualizer_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/code-visualizations", tags=["code-visualizations"])


@router.post("", response_model=CodeVisualizationOut, status_code=status.HTTP_201_CREATED)
def create_visualization(
    payload: CodeVisualizationCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts code directly (pasted independently) OR code forwarded from
    the Converter/Solver's "Visualize this" button -- both are the same
    request shape from the API's point of view, the frontend just
    pre-fills the textarea in the second case.
    """
    return code_visualizer_service.create_and_visualize(db, user_id=current_user.id, payload=payload)


@router.get("", response_model=list[CodeVisualizationOut])
def list_visualizations(
    db: psycopg.Connection = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return code_visualizer_service.list_visualizations_for_user(db, user_id=current_user.id)


@router.get("/{visualization_id}", response_model=CodeVisualizationOut)
def get_visualization(
    visualization_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return code_visualizer_service.get_visualization_for_user(
            db, user_id=current_user.id, visualization_id=visualization_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{visualization_id}", response_model=CodeVisualizationOut)
def update_visualization(
    visualization_id: str,
    payload: CodeVisualizationUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return code_visualizer_service.update_visualization(
            db, user_id=current_user.id, visualization_id=visualization_id, payload=payload
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{visualization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_visualization(
    visualization_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        code_visualizer_service.delete_visualization(
            db, user_id=current_user.id, visualization_id=visualization_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
