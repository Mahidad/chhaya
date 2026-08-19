from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConceptMapCreate(BaseModel):
    title: str = Field(..., min_length=1)
    source_text: str = Field(..., min_length=1)
    source_kind: str = "text"  # "text" | "code" | "math"


class ConceptMapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    source_kind: str
    source_text: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    created_at: datetime
