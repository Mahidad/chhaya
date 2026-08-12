"""Module 2 endpoints for a student's spaced-repetition review schedule."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.review_schedule import ReminderCheckOut, ReviewRatingIn, ReviewScheduleOut
from app.services import review_schedule_service

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/study-guides/{study_guide_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_study_guide_to_schedule(
    study_guide_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add one of the current student's guides to the review schedule.

    Repeating this request is safe: the database unique constraint prevents
    duplicate schedule entries for the same guide.
    """
    review_schedule_service.create_review_from_study_guide(
        db, user_id=current_user.id, study_guide_id=study_guide_id
    )


@router.get("", response_model=list[ReviewScheduleOut])
def list_review_schedules(
    status_filter: str = Query("all", alias="status", pattern="^(due|upcoming|all)$"),
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return review_schedule_service.list_reviews(
        db, user_id=current_user.id, status=status_filter
    )


@router.put("/{review_id}/rate", response_model=ReviewScheduleOut)
def rate_review_schedule(
    review_id: str,
    payload: ReviewRatingIn,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = review_schedule_service.rate_review(
        db, user_id=current_user.id, review_id=review_id, quality=payload.quality
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review_schedule(
    review_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    removed = review_schedule_service.remove_review(
        db, user_id=current_user.id, review_id=review_id
    )
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")


@router.post("/reminders/check", response_model=ReminderCheckOut)
def check_review_reminders(
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the simple daily due-review reminder check for the current student."""
    return review_schedule_service.check_due_reminders(db, user_id=current_user.id)
