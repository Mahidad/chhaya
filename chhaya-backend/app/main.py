from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, engine
import app.models  # noqa: F401 - registers every model on Base.metadata

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def on_startup():
    """
    Dev convenience: creates any missing tables on boot.
    Once the team is comfortable with Alembic (see /alembic), switch to
    running `alembic upgrade head` instead of relying on this, especially
    once there's real data you don't want to risk resetting. This line is
    harmless either way -- it only creates tables that don't exist yet.
    """
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
