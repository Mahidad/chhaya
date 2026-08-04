"""
Orchestration for Amiyo's Feature 1: weak learning areas.

Notice this file has no "create_and_process" pipeline like the other
three -- there's no external API to call, no file to fetch, no AI
generation. It's pure aggregation over data that's already in the
database. Not every feature needs the ingest-then-process shape; this one
is a good example of a service that's "just a query with a rule applied,"
and that's a completely legitimate shape too.
"""

from collections import defaultdict

import psycopg

from app.repositories.quiz_result_respository import quiz_result_repository
from app.schemas.quiz_result import QuizResultCreate, WeakTopic

WEAK_THRESHOLD_PERCENT = 60.0


def record_quiz_result(
    db: psycopg.Connection, *, user_id: str, payload: QuizResultCreate
):
    return quiz_result_repository.create(
        db,
        obj_in={
            "user_id": user_id,
            "topic": payload.topic,
            "course": payload.course,
            "score_percent": payload.score_percent,
        },
    )


def get_weak_topics(
    db: psycopg.Connection,
    *,
    user_id: str,
    threshold: float = WEAK_THRESHOLD_PERCENT,
) -> list[WeakTopic]:
    results = quiz_result_repository.list_for_user(db, user_id=user_id)

    # Group every attempt by topic, so a topic taken 3 times becomes one
    # averaged row instead of 3 separate ones -- "consistently falls
    # below" (per the functional requirements doc) means the average, not
    # any single bad attempt.
    grouped: dict[str, list] = defaultdict(list)
    for r in results:
        grouped[r.topic].append(r)

    topics = []
    for topic, attempts in grouped.items():
        avg = sum(a.score_percent for a in attempts) / len(attempts)
        topics.append(
            WeakTopic(
                topic=topic,
                course=attempts[0].course,
                average_score=round(avg, 1),
                attempts=len(attempts),
                is_weak=avg < threshold,
            )
        )

    # Weakest first -- that's what the dashboard should lead with.
    topics.sort(key=lambda t: t.average_score)
    return topics
