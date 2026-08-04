"""
TeacherProfile dataclass — replaces the SQLAlchemy ORM model.

`raw_style_profile` is stored as JSONB in PostgreSQL.  psycopg v3 deserialises
JSONB columns into Python dicts automatically on read; the base repository
wraps dict values in `psycopg.types.json.Jsonb` on write so the driver knows
to use JSON serialisation rather than repr().
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TeacherProfile:
    id: str
    user_id: str
    source_id: str
    display_name: str
    created_at: datetime
    is_favorite: bool = False
    pacing: str | None = None
    vocabulary_level: str | None = None
    analogy_frequency: str | None = None
    example_density: str | None = None
    raw_style_profile: dict | None = None
