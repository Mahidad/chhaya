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

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Chhaya API"
    ENV: str = "development"  # development | production
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    # Default is SQLite so a new teammate can `uvicorn app.main:app` with
    # zero setup. Swap to Postgres for real use:
    # postgresql+psycopg2://user:password@localhost:5432/chhaya
    DATABASE_URL: str = "sqlite:///./chhaya.db"

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = "change-this-in-your-.env-file"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- CORS (so the Vite dev server on :5173 can call this API) ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # --- External AI / ingestion services ---
    GEMINI_API_KEY: str | None = None
    # If no key is set yet, the teaching-style service falls back to a
    # deterministic mock so the rest of the team can build against a
    # realistic response shape without waiting on a key. See
    # app/services/teaching_style_service.py
    GEMINI_MODEL: str = "gemini-2.0-flash"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """
    Cached so the .env file is parsed once, not on every request.
    Import `settings` (below) everywhere instead of calling this directly.
    """
    return Settings()


settings = get_settings()
