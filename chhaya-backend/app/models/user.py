"""
User dataclass — replaces the SQLAlchemy ORM model.

Field names are identical to the old Column names so Pydantic schemas
(which use `from_attributes=True`) continue to work unchanged.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: str
    full_name: str
    email: str
    hashed_password: str
    created_at: datetime
