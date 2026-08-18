"""
CodeConversion dataclass -- one row per translate/solve request. See
sql/schema.sql for the column-level reasoning.
"""

from dataclasses import dataclass
from datetime import datetime


class ConversionMode:
    TRANSLATE = "translate"
    SOLVE = "solve"


class ConversionStatus:
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


SUPPORTED_LANGUAGES = ["python", "java", "cpp", "javascript", "c"]


@dataclass
class CodeConversion:
    id: str
    user_id: str
    mode: str
    target_language: str
    status: str
    created_at: datetime
    source_language: str | None = None
    source_code: str | None = None
    problem_statement: str | None = None
    code_style_profile_id: str | None = None
    folder_id: str | None = None
    title: str | None = None
    is_favorite: bool = False
    error_message: str | None = None
    output_code: str | None = None
    mapping: list | None = None
    explanation: str | None = None
