"""Simple database row models for the Study Groups feature."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class StudyGroup:
    id: str
    creator_id: str
    name: str
    description: str
    created_at: datetime


@dataclass
class GroupInvitation:
    id: str
    group_id: str
    invited_user_id: str
    invited_by_user_id: str
    status: str
    created_at: datetime


@dataclass
class JoinRequest:
    id: str
    group_id: str
    user_id: str
    status: str
    created_at: datetime
