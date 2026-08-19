"""API request and response shapes for study groups."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class StudyGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)


class InviteCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class StatusUpdate(BaseModel):
    status: str  # accepted | rejected


class StudyGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    creator_id: str
    creator_name: str
    member_count: int
    membership_status: str | None = None
    created_at: datetime


class GroupMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: str
    email: str


class InvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    group_id: str
    group_name: str
    group_description: str
    invited_by_name: str
    status: str
    created_at: datetime


class JoinRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    full_name: str
    email: str
    status: str
    created_at: datetime


class StudyGroupDetailOut(StudyGroupOut):
    members: list[GroupMemberOut]
    join_requests: list[JoinRequestOut]
