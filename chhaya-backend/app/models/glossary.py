"""
GlossaryEntry dataclass -- Module 2's Word Lookup & Personal Glossary
(Lamia). `source` distinguishes a definition pulled straight from the
local WordNet lookup (see app/utils/dictionary.py) from one the student
edited by hand, so the UI can show "from WordNet" vs "edited" without
guessing.
"""

from dataclasses import dataclass
from datetime import datetime


class GlossarySource:
    WORDNET = "wordnet"
    CUSTOM = "custom"


@dataclass
class GlossaryEntry:
    id: str
    user_id: str
    chapter_id: str
    term: str
    definition: str
    source: str
    created_at: datetime
    part_of_speech: str | None = None
