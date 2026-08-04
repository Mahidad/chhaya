"""
Business logic for signup/login. Routes call this; this calls the
repository. This is also a good template for how thin a service can be
when the logic really is simple -- not every service needs to be huge.
"""

import psycopg

from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate
from app.utils.exceptions import PermissionDeniedError


def signup(db: psycopg.Connection, payload: UserCreate):
    existing = user_repository.get_by_email(db, payload.email)
    if existing:
        raise ValueError("An account with this email already exists.")

    user = user_repository.create(
        db,
        obj_in={
            "full_name": payload.full_name,
            "email": payload.email,
            "hashed_password": hash_password(payload.password),
        },
    )
    return user


def login(db: psycopg.Connection, email: str, password: str) -> str:
    """Returns a signed JWT access token, or raises PermissionDeniedError."""
    user = user_repository.get_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise PermissionDeniedError("Incorrect email or password.")
    return create_access_token(subject=user.id)
