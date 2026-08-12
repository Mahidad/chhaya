from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PreferenceProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pacing_score: float
    vocabulary_score: float
    analogy_score: float
    example_score: float
    profile_count: int
    updated_at: datetime
