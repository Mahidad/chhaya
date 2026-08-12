from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CodeStyleProfileCreate(BaseModel):
    """What the "Add coding style" form in the Style Library submits."""
    label: str = Field(..., min_length=1, description="e.g. 'Senior Dev's style'")
    language: str  # one of app.models.code_conversion.SUPPORTED_LANGUAGES
    sample_code: str = Field(..., min_length=1)


class CodeStyleProfileUpdate(BaseModel):
    label: str | None = None
    is_favorite: bool | None = None


class CodeStyleProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    language: str
    indent_style: str
    indent_size: int
    naming_convention: str
    brace_style: str | None
    loop_style: str
    branching_style: str
    cyclomatic_complexity: int
    max_nesting_depth: int
    comment_density: float
    avg_line_length: float
    blank_line_frequency: float
    is_favorite: bool
    created_at: datetime
    # sample_code is intentionally excluded from the list/summary response
    # -- it can be long, and the extracted numbers are what the UI
    # actually displays. Add a GET /{id} with the full schema later if a
    # "view the original sample" screen is ever built.
