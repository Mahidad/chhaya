from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DictionaryLookupOut(BaseModel):
    """Response shape for GET /dictionary/{word} -- not a stored row, just
    the local lookup result, so it has no `id`/`created_at`."""
    word: str
    definition: str
    part_of_speech: str | None
    synonyms: list[str]


class GlossaryEntryCreate(BaseModel):
    chapter_id: str
    term: str
    definition: str
    part_of_speech: str | None = None
    source: str = "wordnet"


class GlossaryEntryUpdate(BaseModel):
    definition: str


class GlossaryEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chapter_id: str
    term: str
    definition: str
    part_of_speech: str | None
    source: str
    created_at: datetime
