from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CodeConversionTranslateCreate(BaseModel):
    source_code: str
    source_language: str | None = None  # None = ask Gemini to auto-detect
    target_language: str
    code_style_profile_id: str | None = None


class CodeConversionSolveCreate(BaseModel):
    problem_statement: str
    target_language: str
    code_style_profile_id: str | None = None


class CodeConversionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mode: str
    source_language: str | None
    target_language: str
    source_code: str | None
    problem_statement: str | None
    code_style_profile_id: str | None
    status: str
    error_message: str | None
    output_code: str | None
    mapping: list[dict[str, Any]] | None
    explanation: str | None
    created_at: datetime
