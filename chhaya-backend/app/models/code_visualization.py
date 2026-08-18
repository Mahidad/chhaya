"""CodeVisualization dataclass -- one row per trace request."""

from dataclasses import dataclass
from datetime import datetime


class VisualizationStatus:
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


@dataclass
class CodeVisualization:
    id: str
    user_id: str
    language: str
    source_code: str
    status: str
    created_at: datetime
    folder_id: str | None = None
    title: str | None = None
    is_favorite: bool = False
    error_message: str | None = None
    trace: list | None = None
    explanation: str | None = None
