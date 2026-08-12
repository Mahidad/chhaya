"""Readable SM-2 scheduling rules and review/reminder orchestration."""

import json
from datetime import date, timedelta
from urllib.error import URLError
from urllib.request import Request, urlopen

import psycopg

from app.core.config import settings
from app.models.review_schedule import ReviewSchedule
from app.repositories import review_schedule_repository


def run_sm2(
    *, quality: int, ease_factor: float, interval_days: int, review_count: int
) -> tuple[float, int, int]:
    """Return (new_ease_factor, new_interval_days, new_review_count)."""
    # Standard SM-2 ease-factor adjustment, never allowing an unusable value.
    new_ease_factor = max(
        1.3,
        ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )

    # Each answer has its own early-review pattern. The ease factor then makes
    # later intervals grow differently too. This is intentionally small and
    # readable rather than a full implementation of every SM-2 variation.
    if quality == 0:  # Again
        return new_ease_factor, 2, 0

    if quality == 2:  # Hard
        if review_count == 0:
            new_interval_days = 3
        elif review_count == 1:
            new_interval_days = 5
        else:
            new_interval_days = max(2, round(interval_days * new_ease_factor * 0.8))
    elif quality == 4:  # Good
        if review_count == 0:
            new_interval_days = 4
        elif review_count == 1:
            new_interval_days = 8
        else:
            new_interval_days = max(2, round(interval_days * new_ease_factor))
    else:  # Easy (quality == 5)
        if review_count == 0:
            new_interval_days = 6
        elif review_count == 1:
            new_interval_days = 12
        else:
            new_interval_days = max(2, round(interval_days * new_ease_factor * 1.3))

    return new_ease_factor, new_interval_days, review_count + 1


def create_review_from_study_guide(
    db: psycopg.Connection, *, user_id: str, study_guide_id: str
) -> ReviewSchedule | None:
    """Called when a student explicitly adds a completed guide; duplicates are ignored."""
    return review_schedule_repository.create_for_study_guide(
        db, user_id=user_id, study_guide_id=study_guide_id
    )


def list_reviews(
    db: psycopg.Connection, *, user_id: str, status: str
) -> list[ReviewSchedule]:
    return review_schedule_repository.list_for_user(db, user_id=user_id, status=status)


def rate_review(
    db: psycopg.Connection, *, user_id: str, review_id: str, quality: int
) -> ReviewSchedule | None:
    review = review_schedule_repository.get_for_user(
        db, review_id=review_id, user_id=user_id
    )
    if review is None:
        return None

    ease_factor, interval_days, review_count = run_sm2(
        quality=quality,
        ease_factor=review.ease_factor,
        interval_days=review.interval_days,
        review_count=review.review_count,
    )
    return review_schedule_repository.update_after_rating(
        db,
        review_id=review_id,
        user_id=user_id,
        ease_factor=ease_factor,
        interval_days=interval_days,
        review_count=review_count,
        next_review_date=date.today() + timedelta(days=interval_days),
    )


def remove_review(
    db: psycopg.Connection, *, user_id: str, review_id: str
) -> bool:
    return review_schedule_repository.delete_for_user(
        db, review_id=review_id, user_id=user_id
    )


def _send_resend_email(*, recipient: str, subject: str, html: str) -> bool:
    """Send through Resend's HTTP API without adding another Python package."""
    if not settings.RESEND_API_KEY or not settings.RESEND_FROM_EMAIL:
        return False

    body = json.dumps(
        {
            "from": settings.RESEND_FROM_EMAIL,
            "to": [recipient],
            "subject": subject,
            "html": html,
        }
    ).encode("utf-8")
    request = Request(
        "https://api.resend.com/emails",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "chhaya-backend/1.0",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except URLError:
        return False


def check_due_reminders(db: psycopg.Connection, *, user_id: str) -> dict[str, int]:
    """Send today's due-review emails once per review; safe to call repeatedly."""
    due_reviews = review_schedule_repository.list_due_for_reminder(db, user_id=user_id)
    sent = 0
    skipped = 0

    for review in due_reviews:
        subject = f"Chhaya review due: {review['topic']}"
        html = (
            f"<p>Hi {review['full_name']},</p>"
            f"<p>Your review for <strong>{review['topic']}</strong> is due today.</p>"
            "<p>Open Chhaya and rate how well you recalled it to schedule the next review.</p>"
        )
        if _send_resend_email(recipient=review["email"], subject=subject, html=html):
            review_schedule_repository.mark_reminded_today(
                db, review_id=review["id"], user_id=user_id
            )
            sent += 1
        else:
            skipped += 1

    return {"checked": len(due_reviews), "sent": sent, "skipped": skipped}
