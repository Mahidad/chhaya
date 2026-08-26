"""
Central configuration for the whole backend.

WHY THIS FILE EXISTS:
Every layer of the app (database, security, external APIs) needs settings
like secret keys, DB URLs, and API keys. Instead of scattering
`os.getenv(...)` calls across the codebase, we read them ONCE here into a
typed `Settings` object. Every other file imports `settings` from here.

This means:
  - one place to see every environment variable the app needs
  - typos in env var names fail fast at startup, not silently at runtime
  - swapping SQLite -> Postgres, or dev -> prod, is a one-line .env change
"""

import json
import os
from functools import lru_cache

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Chhaya API"
    ENV: str = "development"  # development | production
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    # psycopg v3 DSN format: postgresql://USER:PASSWORD@HOST:PORT/DBNAME
    # Copy .env.example to .env and set DATABASE_URL before starting.
    # Run `psql -U <user> -d chhaya -f sql/schema.sql` to create tables.
    DATABASE_URL: str = "postgresql://postgres@localhost:5432/chhaya"

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = "change-this-in-your-.env-file"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- CORS (so the Vite dev server on :5173 can call this API) ---
    # In production this must also list the deployed frontend's origin, or
    # the browser blocks every call. Set CORS_ORIGINS in the environment as a
    # comma-separated list, e.g.
    #   CORS_ORIGINS=https://chhaya.vercel.app,http://localhost:5173
    # Preview deployments get their own generated *.vercel.app hostname, so
    # add CORS_ORIGIN_REGEX if you want those to work too.
    # NoDecode: without it pydantic-settings tries json.loads() on the env
    # value BEFORE any validator runs, so a comma-separated string raises
    # SettingsError and the app refuses to boot. NoDecode hands the raw
    # string to _split_origins below instead.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    # Optional regex alternative, e.g. r"https://.*\.vercel\.app"
    CORS_ORIGIN_REGEX: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        """Accept a plain comma-separated string from the environment.

        pydantic-settings otherwise insists on JSON for list fields, which
        is an easy thing to get wrong in a hosting dashboard -- and getting
        it wrong means the app fails to boot rather than degrading.
        """
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):  # tolerate JSON too, so neither form surprises anyone
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- File uploads ---
    # Notes, exam papers, and generated narration audio are written here.
    # Defaults to <repo>/uploads for local development; in production point
    # it at a mounted persistent disk, because a container's own filesystem
    # is wiped on every deploy and restart.
    UPLOAD_ROOT: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads"
    )

    # --- External AI / ingestion services ---
    GEMINI_API_KEY: str | None = None
    # If no key is set yet, the teaching-style service falls back to a
    # deterministic mock so the rest of the team can build against a
    # realistic response shape without waiting on a key. See
    # app/services/teaching_style_service.py
    GEMINI_MODEL: str | None = None
    OCR_SPACE_API_KEY: str | None = None

    # --- Practice problem bank import ---
    # Kaggle credentials for downloading the practice bank dataset.
    # Get a token at kaggle.com -> Settings -> API -> Create New Token.
    # Alternatively, place kaggle.json in ~/.kaggle/kaggle.json.
    KAGGLE_USERNAME: str | None = None
    KAGGLE_KEY: str | None = None

    # Kaggle dataset the practice bank is imported from. Kept here rather
    # than as a command-line argument so a teammate can run
    # `python scripts/import_practice_problems.py` with no arguments and get
    # the same bank everyone else has -- swapping datasets is then a one-line
    # .env change, not a differently-typed command per person.
    # Not used by the API at runtime, only by that one-time script.
    PRACTICE_DATASET_SLUG: str = "gzipchrist/leetcode-problem-dataset"
    # When true (and ENV=development), a dev server that finds the bank empty
    # imports it in the background so nobody has to run the script by hand.
    # See maybe_import_in_background() in app/services/practice_import_service.py.
    PRACTICE_AUTO_IMPORT: bool = True
    # How often the bank is re-imported from Kaggle so problems added to the
    # upstream dataset appear here too. The scheduled job in render.yaml is
    # the reliable trigger; the startup check uses this same interval as a
    # fallback. The import only ever ADDS -- existing problems and student
    # attempts are never touched.
    PRACTICE_REFRESH_DAYS: int = 7

    # --- Email reminders (Amiyo Module 2) ---
    # Leave unset during local development; the review page still works and
    # reminder checks report skipped emails until Resend is configured.
    RESEND_API_KEY: str | None = None
    RESEND_FROM_EMAIL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """
    Cached so the .env file is parsed once, not on every request.
    Import `settings` (below) everywhere instead of calling this directly.
    """
    return Settings()


settings = get_settings()
