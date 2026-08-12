"""
Pydantic schemas for User.

WHY SCHEMAS ARE SEPARATE FROM THE DB ROW SHAPE:
`app.models.user.User` is the DB row shape -- it has `hashed_password`.
We never, ever want that field in an API response. Pydantic schemas are
the *public contract*: what a request body must look like coming in, and
exactly what fields go out. Keeping them separate from the row dataclass
means "add a column to the DB" and "expose that column in the API" are
two deliberate steps, not one accidental leak.
"""

import re

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

# Kept as one importable list so the frontend's live requirements checklist
# (LoginPage/SignupPage's PasswordField) and this backend validator
# describe the exact same rules in the exact same order -- if these ever
# drift apart, a password the UI shows as "all green" could still get
# rejected by the API.
PASSWORD_REQUIREMENTS = [
    ("At least 8 characters", lambda pw: len(pw) >= 8),
    ("One uppercase letter", lambda pw: re.search(r"[A-Z]", pw) is not None),
    ("One lowercase letter", lambda pw: re.search(r"[a-z]", pw) is not None),
    ("One number", lambda pw: re.search(r"\d", pw) is not None),
    ("One special character (!@#$...)", lambda pw: re.search(r"[^A-Za-z0-9]", pw) is not None),
]


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=1, description="User's full name")
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        failed = [label for label, check in PASSWORD_REQUIREMENTS if not check(value)]
        if failed:
            raise ValueError("Password does not meet requirements: " + "; ".join(failed))
        return value


class UserOut(BaseModel):
    # lets Pydantic read attributes off the User dataclass directly
    # (user.id, user.email, ...) instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: EmailStr
