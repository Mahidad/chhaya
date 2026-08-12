"""
CodeStyleProfile dataclass -- output of app/utils/code_style_analyzer.py,
persisted the same way a TeacherProfile is (see that model's docstring
for why psycopg v3 needs no extra work for the JSONB/dict handling this
one doesn't even need, since every field here is a plain scalar).
"""

from dataclasses import dataclass
from datetime import datetime


class IndentStyle:
    SPACES = "spaces"
    TABS = "tabs"


class NamingConvention:
    SNAKE_CASE = "snake_case"
    CAMEL_CASE = "camelCase"
    PASCAL_CASE = "PascalCase"
    MIXED = "mixed"


class BraceStyle:
    SAME_LINE = "same_line"
    NEXT_LINE = "next_line"


@dataclass
class CodeStyleProfile:
    id: str
    user_id: str
    label: str
    language: str
    indent_style: str
    indent_size: int
    naming_convention: str
    comment_density: float
    avg_line_length: float
    blank_line_frequency: float
    sample_code: str
    created_at: datetime
    brace_style: str | None = None
    loop_style: str = "none"
    branching_style: str = "none"
    cyclomatic_complexity: int = 1
    max_nesting_depth: int = 0
    is_favorite: bool = False
