from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CodeVisualizationCreate(BaseModel):
    source_code: str
    language: str
    folder_id: str | None = None


class CodeVisualizationUpdate(BaseModel):
    title: str | None = None
    is_favorite: bool | None = None
    folder_id: str | None = None


class CodeVisualizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    language: str
    source_code: str
    folder_id: str | None
    title: str | None
    is_favorite: bool
    status: str
    error_message: str | None
    trace: list[dict[str, Any]] | None
    explanation: str | None
    created_at: datetime
