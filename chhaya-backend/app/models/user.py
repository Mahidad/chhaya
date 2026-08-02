"""
The `User` table. Every other table (reference sources, profiles, quizzes,
progress...) will eventually have a `user_id` foreign key pointing here,
because Chhaya's whole premise is a *personal* tutor per student.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # One user -> many reference sources. `cascade="all, delete-orphan"`
    # means deleting a user cleans up their sources too, instead of leaving
    # orphaned rows behind.
    reference_sources = relationship(
        "ReferenceSource", back_populates="owner", cascade="all, delete-orphan"
    )
