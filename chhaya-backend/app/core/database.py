"""
Sets up the SQLAlchemy engine and session factory.

WHY THIS FILE EXISTS:
Every repository (app/repositories/*) needs a `Session` to talk to the
database. Rather than each file creating its own connection, they all pull
a session from `get_db()`, which FastAPI calls automatically per-request via
`Depends(get_db)`.

Think of `engine` as the phone line to Postgres, and each `Session` as one
phone call: opened at the start of a request, used for however many
queries that request needs, then always hung up (closed) in the `finally`
block below -- even if the request raised an error halfway through.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite needs this flag to allow use across FastAPI's threadpool.
    # Postgres doesn't need it, so we only set it conditionally.
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Every SQLAlchemy model (app/models/*) inherits from this Base so that
# Base.metadata knows about every table for create_all() / Alembic.
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields one DB session per request, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
