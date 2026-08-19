"""Simple database row models for the Study Groups feature."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StudyGroup:
    id: str
    creator_id: str
    name: str
    description: str
    created_at: datetime
    creator_name: str | None = None
    member_count: int = 0
    membership_status: str | None = None
    members: list["StudyGroupMember"] = field(default_factory=list)
    join_requests: list["JoinRequest"] = field(default_factory=list)


@dataclass
class StudyGroupMember:
    user_id: str
    full_name: str
    email: str


@dataclass
class GroupInvitation:
    id: str
    group_id: str
    invited_user_id: str
    invited_by_user_id: str
    status: str
    created_at: datetime
    group_name: str | None = None
    group_description: str | None = None
    invited_by_name: str | None = None


@dataclass
class JoinRequest:
    id: str
    group_id: str
    user_id: str
    status: str
    created_at: datetime
    full_name: str | None = None
    email: str | None = None
