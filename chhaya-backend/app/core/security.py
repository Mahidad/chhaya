"""
Password hashing and JWT helpers.

WHY THIS FILE EXISTS:
Auth logic (how a password is hashed, how a token is signed) should live
in exactly one place. If we ever switch from bcrypt to argon2, or change
token expiry, we change it here -- not in five different route files.

Nothing in here talks to the database or FastAPI. It's pure functions:
give it a password, get a hash back. Give it a user id, get a token back.
That makes it trivial to unit test without spinning up the whole app.
"""

from datetime import datetime, timedelta, timezone

import jwt
import bcrypt
from app.core.config import settings

def hash_password(plain_password: str) -> str:
    pw_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pw_bytes, hashed_bytes)


def create_access_token(subject: str) -> str:
    """
    `subject` is normally the user's id (as a string). We embed it as the
    JWT's `sub` claim so that later, on every authenticated request, we can
    decode the token and know who's calling without hitting the DB twice.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Returns the user id embedded in the token, or None if invalid/expired."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
