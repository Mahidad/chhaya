"""ConceptMap dataclass -- Module 3 Feature 2 (Lamia)."""

from dataclasses import dataclass
from datetime import datetime


class SourceKind:
    TEXT = "text"
    CODE = "code"
    MATH = "math"


@dataclass
class ConceptMap:
    id: str
    user_id: str
    title: str
    source_kind: str
    source_text: str
    nodes: list
    edges: list
    created_at: datetime
