"""
ConceptMap and ConceptMapAttempt dataclasses -- Module 3's active-recall
game (Lamia).
"""

from dataclasses import dataclass
from datetime import datetime


class ExtractionMode:
    TEXT = "text"        # NLTK sentence/POS extraction -- general prose
    FORMULA = "formula"  # regex variable/operator extraction -- math


class ConceptMapStatus:
    READY = "ready"
    FAILED = "failed"


@dataclass
class ConceptMap:
    id: str
    user_id: str
    title: str
    extraction_mode: str
    items: list          # [{id, template, answer}, ...] -- see concept_extraction.py
    is_basic_mode: bool
    status: str
    created_at: datetime
    chapter_id: str | None = None
    source_content_type: str | None = None
    source_content_id: str | None = None
    error_message: str | None = None


@dataclass
class ConceptMapAttempt:
    id: str
    user_id: str
    concept_map_id: str
    correct_count: int
    total_count: int
    completed_at: datetime
