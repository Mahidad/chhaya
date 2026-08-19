import psycopg
from psycopg.rows import dict_row

from app.models.voice_narration import VoiceNarration
from app.repositories.base import BaseRepository


class VoiceNarrationRepository(BaseRepository[VoiceNarration]):
    _table = "voice_narrations"
    _model = VoiceNarration

    def get_for_user(
        self, db: psycopg.Connection, *, narration_id: str, user_id: str
    ) -> VoiceNarration | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM voice_narrations WHERE id = %s AND user_id = %s",
                (narration_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())

    def get_for_note(self, db: psycopg.Connection, *, note_id: str, user_id: str) -> VoiceNarration | None:
        """Backs the "the generated voice is saved unless regenerated" rule --
        the service checks here first and returns the existing narration
        instead of paying for synthesis again."""
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM voice_narrations
                WHERE note_id = %s AND user_id = %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (note_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())

    def get_for_study_guide(
        self, db: psycopg.Connection, *, study_guide_id: str, user_id: str
    ) -> VoiceNarration | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM voice_narrations
                WHERE study_guide_id = %s AND user_id = %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (study_guide_id, user_id),
            )
            return self._row_to_obj(cur.fetchone())


voice_narration_repository = VoiceNarrationRepository()
