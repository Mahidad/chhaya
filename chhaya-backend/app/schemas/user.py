"""
Pydantic schemas for User.

WHY SCHEMAS ARE SEPARATE FROM MODELS:
`app.models.user.User` is the DB table shape -- it has `hashed_password`.
We never, ever want that field in an API response. Pydantic schemas are
the *public contract*: what a request body must look like coming in, and
exactly what fields go out. Keeping them separate from the SQLAlchemy
model means "add a column to the DB" and "expose that column in the API"
are two deliberate steps, not one accidental leak.
"""

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    # lets Pydantic read attributes off a SQLAlchemy object directly
    # (model.id, model.email, ...) instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: EmailStr
