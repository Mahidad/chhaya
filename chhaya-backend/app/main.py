from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import pool
from app.services import practice_import_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Opens the connection pool on startup and drains it on shutdown.

    `wait=True` means the app won't start accepting requests until at
    least one connection to PostgreSQL is confirmed healthy -- better to
    fail fast at boot than to surface DB errors on the first real request.

    Replaces the old `@app.on_event("startup")` + Base.metadata.create_all
    pattern. Table creation is now handled outside the app by running:
        psql -U <user> -d chhaya -f sql/schema.sql

    The practice-bank check below is data, not DDL: it only fills an
    already-created table, only in development, only when that table is
    empty, and it does its work on a background thread so startup is not
    delayed. It never raises -- see app/services/practice_import_service.py.
    """
    pool.open(wait=True)
    practice_import_service.maybe_import_in_background()
    yield
    pool.close()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
