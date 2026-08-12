"""
Repository for the one-row-per-user preference_profiles table.

WHY A CUSTOM `upsert` INSTEAD OF THE INHERITED create()/update():
The base class's `create()` always generates a fresh id and INSERTs --
fine for every other table, wrong here, since a user's preference profile
should be recomputed IN PLACE, not accumulated as new rows every time a
profile is added to their library. `upsert` uses Postgres's native
`INSERT ... ON CONFLICT (user_id) DO UPDATE` so "does a row exist yet for
this user" and "write the new numbers" happen as one atomic statement,
instead of a separate SELECT-then-branch that could race with itself.
"""

import uuid

import psycopg
from psycopg.rows import dict_row

from app.models.preference_profile import PreferenceProfile
from app.repositories.base import BaseRepository


class PreferenceProfileRepository(BaseRepository[PreferenceProfile]):
    _table = "preference_profiles"
    _model = PreferenceProfile

    def get_by_user(self, db: psycopg.Connection, *, user_id: str) -> PreferenceProfile | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM preference_profiles WHERE user_id = %s",
                (user_id,),
            )
            return self._row_to_obj(cur.fetchone())

    def upsert(
        self,
        db: psycopg.Connection,
        *,
        user_id: str,
        pacing_score: float,
        vocabulary_score: float,
        analogy_score: float,
        example_score: float,
        profile_count: int,
    ) -> PreferenceProfile:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO preference_profiles
                    (id, user_id, pacing_score, vocabulary_score, analogy_score, example_score, profile_count, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    pacing_score = EXCLUDED.pacing_score,
                    vocabulary_score = EXCLUDED.vocabulary_score,
                    analogy_score = EXCLUDED.analogy_score,
                    example_score = EXCLUDED.example_score,
                    profile_count = EXCLUDED.profile_count,
                    updated_at = NOW()
                RETURNING *
                """,
                (
                    str(uuid.uuid4()),
                    user_id,
                    pacing_score,
                    vocabulary_score,
                    analogy_score,
                    example_score,
                    profile_count,
                ),
            )
            return self._row_to_obj(cur.fetchone())


preference_profile_repository = PreferenceProfileRepository()
