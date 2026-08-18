import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.code_workspace_folder import (
    CodeWorkspaceFolderCreate,
    CodeWorkspaceFolderOut,
    CodeWorkspaceFolderUpdate,
)
from app.services import code_workspace_folder_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/code-workspace-folders", tags=["code-workspace-folders"])


@router.post("", response_model=CodeWorkspaceFolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: CodeWorkspaceFolderCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return code_workspace_folder_service.create_folder(db, user_id=current_user.id, payload=payload)


@router.get("", response_model=list[CodeWorkspaceFolderOut])
def list_folders(
    db: psycopg.Connection = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return code_workspace_folder_service.list_folders_for_user(db, user_id=current_user.id)


@router.patch("/{folder_id}", response_model=CodeWorkspaceFolderOut)
def rename_folder(
    folder_id: str,
    payload: CodeWorkspaceFolderUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return code_workspace_folder_service.rename_folder(
            db, user_id=current_user.id, folder_id=folder_id, payload=payload
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Un-files the folder's contents first (they go back to Unfiled),
    then deletes the folder itself -- see code_workspace_folder_service.py."""
    try:
        code_workspace_folder_service.delete_folder(db, user_id=current_user.id, folder_id=folder_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
