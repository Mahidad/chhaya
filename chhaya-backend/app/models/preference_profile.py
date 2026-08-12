"""
PreferenceProfile dataclass — one row per user, upserted (never appended
to). Represents "what this student's taste actually looks like" as four
numeric scores on the same 0-100 scale the frontend already uses for
style meters, so it can be compared directly against any teacher
profile's scores with plain subtraction. See
app/services/preference_service.py for how it's computed.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PreferenceProfile:
    id: str
    user_id: str
    pacing_score: float
    vocabulary_score: float
    analogy_score: float
    example_score: float
    profile_count: int
    updated_at: datetime
