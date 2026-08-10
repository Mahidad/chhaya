"""
Combines every module's router into one. When Omar, Lamia, and Amiyo add
their endpoints (exams.py, study_guides.py, progress.py...), they each add
one line here -- main.py never needs to change again.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    reference_sources,
    teacher_profiles,
    study_guides,
    exam_papers,
    likely_questions,
    progress,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(reference_sources.router)
api_router.include_router(teacher_profiles.router)
api_router.include_router(study_guides.router)
api_router.include_router(exam_papers.router)
api_router.include_router(likely_questions.router)
api_router.include_router(progress.router)
