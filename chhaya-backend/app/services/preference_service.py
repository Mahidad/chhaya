"""
The "preference profile" feature: a per-student, weighted-average style
fingerprint built from their Style Library, used to score how well any
candidate teacher profile (a source they're considering, or already have)
matches what they actually tend to prefer.

DELIBERATELY NO AI CALL ANYWHERE IN THIS FILE. Both functions here are
plain arithmetic over numbers already sitting in Postgres -- a weighted
mean and a distance calculation. That's not a simplification for time's
sake; it's the point: this is the kind of feature you can build, explain,
and reproduce by hand in the no-AI live exam, unlike the Gemini-backed
parts of the app.

HOW "PREFERENCE" IS WEIGHTED (the crude, explainable heuristic):
Every profile in the library counts for something just by being there
(base weight 1) -- adding a source is a mild positive signal on its own.
On top of that:
  - +2 if the student favorited/pinned it in the Style Library (a
    deliberate, stated preference)
  - +1 for every study guide generated using that profile (a *revealed*
    preference -- actually choosing to use a style repeatedly is a
    stronger signal than passively leaving it in the library)
A profile the student pinned AND used for 4 study guides ends up weighted
7x as heavily in the average as one just sitting unused in the library.

KNOWN LIMITATION, STATED HONESTLY: with only one or two profiles in the
library, the "preference" is really just an average of whatever's there
-- it hasn't had a chance to reflect real taste yet. It gets more
meaningful as the student favorites/uses things. This is a genuine
cold-start limitation of any preference system built from usage data, not
a bug to hide.
"""

import psycopg
from psycopg.rows import dict_row

from app.repositories.preference_profile_repository import preference_profile_repository

# Maps the categorical labels Gemini (or the mock fallback) returns onto
# the same 0-100 scale the frontend already uses for its style meters
# (see chhaya-frontend's SourceDetailPage.jsx, LEVEL_TO_PERCENT) -- one
# shared vocabulary between "how a meter is drawn" and "how two styles
# are numerically compared".
LEVEL_TO_SCORE = {
    "low": 30, "slow": 30, "beginner": 30,
    "medium": 60, "moderate": 60, "intermediate": 60,
    "high": 88, "fast": 88, "advanced": 88,
}


def _score(level: str | None) -> float:
    if not level:
        return 60.0  # unknown -> assume "medium", a neutral midpoint
    return LEVEL_TO_SCORE.get(level.lower(), 60.0)


def recompute_preference_profile(db: psycopg.Connection, *, user_id: str) -> None:
    """
    Recomputes and upserts this user's preference_profiles row from
    scratch, from whatever's currently in their Style Library. Called
    after: a new teacher_profile is created (ingestion finishes), and
    whenever a profile's is_favorite flag changes (see
    teacher_profile_service.py and reference_source_service.py) -- both
    are exactly the moments the weighting formula above depends on.

    Does nothing if the library is empty -- there's nothing to average.
    """
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                tp.pacing, tp.vocabulary_level, tp.analogy_frequency, tp.example_density,
                tp.is_favorite,
                COUNT(sg.id) AS usage_count
            FROM teacher_profiles tp
            LEFT JOIN study_guides sg ON sg.teacher_profile_id = tp.id
            WHERE tp.user_id = %s
            GROUP BY tp.id
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    if not rows:
        return

    total_weight = 0.0
    weighted_pacing = weighted_vocab = weighted_analogy = weighted_example = 0.0

    for row in rows:
        weight = 1 + (2 if row["is_favorite"] else 0) + row["usage_count"]
        total_weight += weight
        weighted_pacing += weight * _score(row["pacing"])
        weighted_vocab += weight * _score(row["vocabulary_level"])
        weighted_analogy += weight * _score(row["analogy_frequency"])
        weighted_example += weight * _score(row["example_density"])

    preference_profile_repository.upsert(
        db,
        user_id=user_id,
        pacing_score=weighted_pacing / total_weight,
        vocabulary_score=weighted_vocab / total_weight,
        analogy_score=weighted_analogy / total_weight,
        example_score=weighted_example / total_weight,
        profile_count=len(rows),
    )


def compute_match_score(preference, profile) -> float:
    """
    0-100: how closely one teacher_profile's style matches the student's
    preference profile. 100 = identical on all four dimensions, 0 = as
    different as the 0-100 scale allows.

    Plain mean absolute difference across the four dimensions, inverted --
    deliberately not a fancier distance metric (Euclidean, cosine, etc.).
    Mean-abs-difference is easy to compute by hand, easy to explain to a
    non-technical reader ("on average, how many points apart"), and
    that transparency matters more here than a marginally more
    "sophisticated" formula would.
    """
    diffs = [
        abs(preference.pacing_score - _score(profile.pacing)),
        abs(preference.vocabulary_score - _score(profile.vocabulary_level)),
        abs(preference.analogy_score - _score(profile.analogy_frequency)),
        abs(preference.example_score - _score(profile.example_density)),
    ]
    avg_diff = sum(diffs) / len(diffs)
    return round(max(0.0, 100.0 - avg_diff), 1)


def get_preference_profile(db: psycopg.Connection, *, user_id: str):
    return preference_profile_repository.get_by_user(db, user_id=user_id)
