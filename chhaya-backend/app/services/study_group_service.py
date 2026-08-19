"""Business rules for creating, joining, inviting, and deleting study groups."""

import psycopg

from app.models.study_group import GroupInvitation, StudyGroup
from app.repositories.study_group_repository import study_group_repository
from app.repositories.user_repository import user_repository
from app.utils.exceptions import NotFoundError, PermissionDeniedError


def create_group(
    db: psycopg.Connection, *, user_id: str, name: str, description: str
) -> StudyGroup:
    group = study_group_repository.create_with_creator(
        db,
        creator_id=user_id,
        name=name.strip(),
        description=description.strip(),
    )
    return get_group_detail(db, group_id=group.id, user_id=user_id)


def list_groups(db: psycopg.Connection, *, user_id: str) -> list[StudyGroup]:
    return study_group_repository.list_for_user(db, user_id=user_id)


def get_group_detail(
    db: psycopg.Connection, *, group_id: str, user_id: str
) -> StudyGroup:
    group = study_group_repository.get_for_user(
        db, group_id=group_id, user_id=user_id
    )
    if not group:
        raise NotFoundError("Study group not found.")
    group.members = study_group_repository.list_members(db, group_id=group_id)
    group.join_requests = (
        study_group_repository.list_join_requests(db, group_id=group_id)
        if group.creator_id == user_id
        else []
    )
    return group


def invite_student(
    db: psycopg.Connection, *, group_id: str, creator_id: str, email: str
) -> None:
    group = study_group_repository.get_for_user(
        db, group_id=group_id, user_id=creator_id
    )
    if not group:
        raise NotFoundError("Study group not found.")
    if group.creator_id != creator_id:
        raise PermissionDeniedError("Only the group creator can invite students.")
    student = user_repository.get_by_email(db, email.strip().lower())
    if not student:
        raise NotFoundError("No student exists with that email address.")
    study_group_repository.create_invitation(
        db,
        group_id=group_id,
        invited_user_id=student.id,
        invited_by_user_id=creator_id,
    )


def list_invitations(
    db: psycopg.Connection, *, user_id: str
) -> list[GroupInvitation]:
    return study_group_repository.list_invitations(db, user_id=user_id)


def respond_to_invitation(
    db: psycopg.Connection, *, invitation_id: str, user_id: str, status: str
) -> None:
    invitation = study_group_repository.get_invitation(
        db, invitation_id=invitation_id, user_id=user_id
    )
    if not invitation:
        raise NotFoundError("Invitation not found.")
    if invitation.status != "pending":
        raise ValueError("This invitation has already been answered.")
    study_group_repository.update_invitation(
        db, invitation_id=invitation_id, status=status
    )
    if status == "accepted":
        study_group_repository.add_member(
            db, group_id=invitation.group_id, user_id=user_id
        )


def request_to_join(
    db: psycopg.Connection, *, group_id: str, user_id: str
) -> None:
    group = study_group_repository.get_for_user(
        db, group_id=group_id, user_id=user_id
    )
    if not group:
        raise NotFoundError("Study group not found.")
    if group.membership_status == "member":
        raise ValueError("You are already a member of this group.")
    study_group_repository.create_join_request(db, group_id=group_id, user_id=user_id)


def respond_to_join_request(
    db: psycopg.Connection,
    *,
    group_id: str,
    request_id: str,
    creator_id: str,
    status: str,
) -> None:
    group = study_group_repository.get_for_user(
        db, group_id=group_id, user_id=creator_id
    )
    if not group or group.creator_id != creator_id:
        raise PermissionDeniedError("Only the group creator can respond to requests.")
    request = study_group_repository.get_join_request(
        db, request_id=request_id, group_id=group_id
    )
    if not request:
        raise NotFoundError("Join request not found.")
    study_group_repository.update_join_request(
        db, request_id=request_id, status=status
    )
    if status == "accepted":
        study_group_repository.add_member(
            db, group_id=group_id, user_id=request.user_id
        )


def delete_group(
    db: psycopg.Connection, *, group_id: str, creator_id: str
) -> None:
    group = study_group_repository.get_for_user(
        db, group_id=group_id, user_id=creator_id
    )
    if not group:
        raise NotFoundError("Study group not found.")
    if group.creator_id != creator_id:
        raise PermissionDeniedError("Only the group creator can delete this group.")
    study_group_repository.delete(db, id=group_id)
