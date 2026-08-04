"""
Shared dependencies every protected route needs.  `get_current_user` is
what turns "Authorization: Bearer <token>" into an actual `User` row --
every endpoint that should require login just adds
`current_user: User = Depends(get_current_user)` to its signature.
"""

import psycopg
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import user_repository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: psycopg.Connection = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_error

    user = user_repository.get(db, user_id)
    if user is None:
        raise credentials_error
    return user
