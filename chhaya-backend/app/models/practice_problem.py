"""
PracticeProblem -- shared reference data (no user_id), imported once from
a public LeetCode dataset. See sql/schema.sql's comment on this table for
why it's a static import rather than a live mirror of leetcode.com.
"""

from dataclasses import dataclass
from datetime import datetime


class Difficulty:
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class PracticeProblem:
    id: str
    title: str
    title_slug: str
    difficulty: str
    description: str
    created_at: datetime
    topic_tags: list | None = None
