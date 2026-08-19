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
    code_style_profiles, 
    code_conversions,
    code_visualizations,
    code_workspace_folders,
    practice,
    study_guides,
    exam_papers,
    likely_questions,
    progress,
    review_schedules,
    annotations,
    courses,
    glossary,
    notes,
    quizzes,
    voice_narrations,
    concept_maps,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(reference_sources.router)
api_router.include_router(teacher_profiles.router)
api_router.include_router(code_style_profiles.router)
api_router.include_router(code_conversions.router)
api_router.include_router(code_visualizations.router)
api_router.include_router(code_workspace_folders.router)
api_router.include_router(practice.router)
api_router.include_router(study_guides.router)
api_router.include_router(exam_papers.router)
api_router.include_router(likely_questions.router)
api_router.include_router(progress.router)
api_router.include_router(review_schedules.router)
api_router.include_router(annotations.router)
api_router.include_router(courses.router)
api_router.include_router(courses.chapters_router)
api_router.include_router(glossary.router)
api_router.include_router(notes.router)
api_router.include_router(quizzes.router)
api_router.include_router(voice_narrations.router)
api_router.include_router(concept_maps.router)
