import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import pool
from app.utils.exceptions import ExternalServiceError
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
    # A misconfigured deploy is by far the most common way this fails, and
    # the raw psycopg error ("connection to 127.0.0.1:5432 refused") does not
    # make it obvious that the real problem is a missing environment
    # variable. Say so plainly before the pool times out.
    if settings.ENV != "development" and "localhost" in settings.DATABASE_URL:
        print(
            "[startup] DATABASE_URL is still the local development default, so "
            "this will try to reach a database on this container and fail."
        )
        print(
            "[startup] Set DATABASE_URL in your host's environment settings to "
            "your Postgres connection string, then redeploy."
        )

    # Uploads written inside the application directory do not survive a
    # deploy or a restart -- the container filesystem is rebuilt each time.
    # The rows in notes/exam_papers/narrations stay, so the feature looks
    # fine until someone opens an older file and it 404s.
    if settings.ENV != "development" and os.path.abspath(
        settings.UPLOAD_ROOT
    ).startswith(os.path.abspath(os.path.dirname(os.path.dirname(__file__)))):
        print(
            "[startup] UPLOAD_ROOT points inside the application directory "
            f"({settings.UPLOAD_ROOT}), which is wiped on every deploy."
        )
        print(
            "[startup] Point it at a mounted persistent disk (e.g. "
            "UPLOAD_ROOT=/var/data/uploads) or uploaded notes and exam papers "
            "will disappear."
        )

    pool.open(wait=True)
    practice_import_service.maybe_import_in_background()
    yield
    pool.close()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.exception_handler(ExternalServiceError)
def external_service_error_handler(request: Request, exc: ExternalServiceError):
    """Turn an upstream AI/API failure into 503, not 500.

    Gemini returns 503 UNAVAILABLE under load often enough that any feature
    calling it will fail sometimes. Only quizzes.py caught this, so everywhere
    else -- reference source ingestion, style analysis, guide generation --
    surfaced an opaque "500 Internal Server Error" that reads like an
    application bug rather than a busy upstream service.

    503 also tells the frontend the request is worth retrying, which a 500
    does not.
    """
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


@app.get("/health/integrations", tags=["health"])
def integrations_check():
    """Which external services this instance is configured to reach.

    Booleans only -- never the keys themselves. Exists because "the external
    APIs stopped working after deploying" is almost always one unset
    environment variable, and reading it off a running instance beats
    guessing from a dashboard.

    `false` means the feature falls back to a mock or refuses the request;
    `true` means a key is present, NOT that the remote service is healthy or
    that the key is valid.
    """
    try:
        from app.utils.dictionary import _ensure_wordnet

        wordnet = _ensure_wordnet()
    except Exception:
        wordnet = False

    return {
        "env": settings.ENV,
        "database": "localhost" not in settings.DATABASE_URL,
        "gemini": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
        "ocr_space": bool(settings.OCR_SPACE_API_KEY),
        "resend_email": bool(settings.RESEND_API_KEY and settings.RESEND_FROM_EMAIL),
        "kaggle": bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")),
        # False means YouTube requests egress from this host's own IP, which
        # datacenter providers get blocked on.
        "youtube_proxy": bool(
            settings.YOUTUBE_PROXY_URL
            or (settings.WEBSHARE_PROXY_USERNAME and settings.WEBSHARE_PROXY_PASSWORD)
        ),
        # False means uploads live in the app directory and vanish on deploy.
        "uploads_persistent": not os.path.abspath(settings.UPLOAD_ROOT).startswith(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        ),
        "wordnet_corpus": wordnet,
        "upload_root": settings.UPLOAD_ROOT,
    }
