"""FastAPI endpoints for creating and managing study groups."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.study_group import (
    InvitationOut,
    InviteCreate,
    StatusUpdate,
    StudyGroupCreate,
    StudyGroupDetailOut,
    StudyGroupOut,
)
from app.services import study_group_service
from app.utils.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/study-groups", tags=["study-groups"])


@router.post("", response_model=StudyGroupOut, status_code=status.HTTP_201_CREATED)
def create_study_group(
    payload: StudyGroupCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return study_group_service.create_group(
        db,
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )


@router.get("", response_model=list[StudyGroupOut])
def list_study_groups(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return study_group_service.list_groups(db, user_id=current_user.id)


@router.get("/invitations", response_model=list[InvitationOut])
def list_my_invitations(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return study_group_service.list_invitations(db, user_id=current_user.id)


@router.post(
    "/invitations/{invitation_id}/respond", status_code=status.HTTP_204_NO_CONTENT
)
def respond_to_invitation(
    invitation_id: str,
    payload: StatusUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.status not in {"accepted", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be accepted or rejected.",
        )

    try:
        study_group_service.respond_to_invitation(
            db,
            invitation_id=invitation_id,
            user_id=current_user.id,
            status=payload.status,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get("/{group_id}", response_model=StudyGroupDetailOut)
def get_study_group(
    group_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return study_group_service.get_group_detail(
            db, group_id=group_id, user_id=current_user.id
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_study_group(
    group_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        study_group_service.delete_group(
            db, group_id=group_id, creator_id=current_user.id
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.post("/{group_id}/invite", status_code=status.HTTP_204_NO_CONTENT)
def invite_student(
    group_id: str,
    payload: InviteCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        study_group_service.invite_student(
            db,
            group_id=group_id,
            creator_id=current_user.id,
            email=payload.email,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.post("/{group_id}/join-request", status_code=status.HTTP_204_NO_CONTENT)
def request_to_join(
    group_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        study_group_service.request_to_join(
            db, group_id=group_id, user_id=current_user.id
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.post(
    "/{group_id}/join-requests/{request_id}/respond",
    status_code=status.HTTP_204_NO_CONTENT,
)
def respond_to_join_request(
    group_id: str,
    request_id: str,
    payload: StatusUpdate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.status not in {"accepted", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be accepted or rejected.",
        )

    try:
        study_group_service.respond_to_join_request(
            db,
            group_id=group_id,
            request_id=request_id,
            creator_id=current_user.id,
            status=payload.status,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
