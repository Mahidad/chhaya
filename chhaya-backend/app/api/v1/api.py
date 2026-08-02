"""
Combines every module's router into one. When Omar, Lamia, and Amiyo add
their endpoints (exams.py, study_guides.py, progress.py...), they each add
one line here -- main.py never needs to change again.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, reference_sources

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(reference_sources.router)

# Future modules plug in exactly the same way, e.g.:
# from app.api.v1.endpoints import study_guides
# api_router.include_router(study_guides.router)
