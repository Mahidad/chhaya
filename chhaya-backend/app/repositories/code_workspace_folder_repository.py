import psycopg
from psycopg.rows import dict_row

from app.models.code_workspace_folder import CodeWorkspaceFolder
from app.repositories.base import BaseRepository


class CodeWorkspaceFolderRepository(BaseRepository[CodeWorkspaceFolder]):
    _table = "code_workspace_folders"
    _model = CodeWorkspaceFolder

    def list_for_user(self, db: psycopg.Connection, *, user_id: str) -> list[CodeWorkspaceFolder]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM code_workspace_folders WHERE user_id = %s ORDER BY name",
                (user_id,),
            )
            return [self._row_to_obj(row) for row in cur.fetchall()]

    def get_for_user(self, db: psycopg.Connection, *, folder_id: str, user_id: str) -> CodeWorkspaceFolder | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM code_workspace_folders WHERE id = %s AND user_id = %s",
                (folder_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())

    def unfile_contents(self, db: psycopg.Connection, *, folder_id: str) -> None:
        """
        Called before deleting a folder -- un-files everything in it
        (sets folder_id back to NULL) rather than deleting the student's
        saved work. See sql/schema.sql's comment on this table for why
        that's the safer default.
        """
        with db.cursor() as cur:
            cur.execute("UPDATE code_conversions SET folder_id = NULL WHERE folder_id = %s", (folder_id,))
            cur.execute("UPDATE code_visualizations SET folder_id = NULL WHERE folder_id = %s", (folder_id,))


code_workspace_folder_repository = CodeWorkspaceFolderRepository()
