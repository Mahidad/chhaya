"""
CRUD for Code Studio's folders. Deleting a folder un-files its contents
(sets their folder_id back to NULL) rather than deleting the student's
saved conversions/solves/visualizations -- see the repository's
unfile_contents() and the schema comment on code_workspace_folders for
why that's the safer default than a cascading delete.
"""

import psycopg

from app.repositories.code_workspace_folder_repository import code_workspace_folder_repository
from app.schemas.code_workspace_folder import CodeWorkspaceFolderCreate, CodeWorkspaceFolderUpdate
from app.utils.exceptions import NotFoundError


def create_folder(db: psycopg.Connection, *, user_id: str, payload: CodeWorkspaceFolderCreate):
    return code_workspace_folder_repository.create(db, obj_in={"user_id": user_id, "name": payload.name})


def list_folders_for_user(db: psycopg.Connection, *, user_id: str):
    return code_workspace_folder_repository.list_for_user(db, user_id=user_id)


def _get_owned_folder(db: psycopg.Connection, *, user_id: str, folder_id: str):
    folder = code_workspace_folder_repository.get_for_user(db, folder_id=folder_id, user_id=user_id)
    if not folder:
        raise NotFoundError("Folder not found.")
    return folder


def rename_folder(db: psycopg.Connection, *, user_id: str, folder_id: str, payload: CodeWorkspaceFolderUpdate):
    folder = _get_owned_folder(db, user_id=user_id, folder_id=folder_id)
    return code_workspace_folder_repository.update(db, db_obj=folder, obj_in={"name": payload.name})


def delete_folder(db: psycopg.Connection, *, user_id: str, folder_id: str) -> None:
    folder = _get_owned_folder(db, user_id=user_id, folder_id=folder_id)
    code_workspace_folder_repository.unfile_contents(db, folder_id=folder.id)
    code_workspace_folder_repository.delete(db, id=folder.id)
