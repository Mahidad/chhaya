"""
Code Studio's dashboard: solved counts, growth over time, practice
activity, average solve time, and a pseudo-rank.

NO AI ANYWHERE IN THIS FILE -- every number here is aggregation over rows
already in practice_attempts, the same way preference_service.py computes
the style preference fingerprint. That keeps it reproducible by hand and
means the dashboard still works with no GEMINI_API_KEY set.

Computed fresh on each request rather than stored: these are cheap
aggregate queries over one user's own attempts, and a stored copy would
just be another thing that can go stale.
"""

from collections import defaultdict
from datetime import timedelta

import psycopg
from psycopg.rows import dict_row

# Pseudo-ranking thresholds. Points weight *solving* over merely
# attempting, and weight harder problems more -- otherwise grinding easy
# problems would outrank genuine progress. Deliberately simple and
# explainable: a student should be able to work out why they're at a
# given rank.
POINTS_PER_SOLVE = {"easy": 10, "medium": 25, "hard": 50}
RANK_TIERS = [
    (0, "Getting started"),
    (100, "Building momentum"),
    (300, "Steady solver"),
    (700, "Strong problem solver"),
    (1500, "Advanced"),
]


def _rank_for_points(points: int) -> str:
    label = RANK_TIERS[0][1]
    for threshold, tier_label in RANK_TIERS:
        if points >= threshold:
            label = tier_label
    return label


def get_dashboard(db: psycopg.Connection, *, user_id: str) -> dict:
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT pa.is_correct, pa.seconds_taken, pa.started_at, pa.submitted_at,
                   pa.status, pp.difficulty
            FROM practice_attempts pa
            JOIN practice_problems pp ON pp.id = pa.problem_id
            WHERE pa.user_id = %s
            ORDER BY pa.started_at
            """,
            (user_id,),
        )
        rows = cur.fetchall()

        # "Now" has to come from the DATABASE, not datetime.now(timezone.utc).
        # psycopg returns TIMESTAMPTZ columns in the session's timezone
        # (Asia/Dhaka here), so a UTC "now" put the day/week buckets in a
        # different calendar day than the timestamps they were bucketing
        # against -- at 03:24 in Dhaka it is still the previous day in UTC,
        # so today's practice landed on a date key the month loop below
        # never generated and every bar read zero. Taking now() from the
        # same session guarantees both sides share a timezone.
        cur.execute("SELECT now()")
        now = cur.fetchone()["now"]

    submitted = [r for r in rows if r["status"] == "submitted"]
    solved = [r for r in submitted if r["is_correct"] is True]

    # --- headline numbers ---
    total_attempted = len(submitted)
    total_solved = len(solved)
    accuracy = round(100.0 * total_solved / total_attempted, 1) if total_attempted else 0.0

    solve_times = [r["seconds_taken"] for r in solved if r["seconds_taken"] is not None]
    avg_seconds = round(sum(solve_times) / len(solve_times), 1) if solve_times else None

    by_difficulty = defaultdict(int)
    for r in solved:
        by_difficulty[r["difficulty"]] += 1

    # --- growth: cumulative solves per ISO week, last 12 weeks ---
    # %G not %Y: %V is the ISO week number and only lines up with the ISO
    # year. Pairing it with the calendar year mislabels the turn of the
    # year -- 2027-01-01 is ISO 2026-W53, which %Y-W%V would write as
    # "2027-W53", a key nothing else ever produces, silently dropping those
    # solves from the chart.
    weekly = defaultdict(int)
    for r in solved:
        submitted_at = r["submitted_at"] or r["started_at"]
        weekly[submitted_at.strftime("%G-W%V")] += 1

    # The window shows 12 weeks, but the line is labelled *cumulative*, so
    # it has to start from everything solved before the window rather than
    # from zero -- otherwise a long-time user's total appears to reset every
    # quarter.
    window_start = now - timedelta(weeks=11)
    window_start = (window_start - timedelta(days=window_start.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    running_total = sum(
        1 for r in solved if (r["submitted_at"] or r["started_at"]) < window_start
    )

    growth = []
    for offset in range(11, -1, -1):
        key = (now - timedelta(weeks=offset)).strftime("%G-W%V")
        running_total += weekly.get(key, 0)
        growth.append({"week": key, "solved_that_week": weekly.get(key, 0), "cumulative": running_total})

    # --- activity: minutes practiced per day, current calendar month ---
    daily_seconds = defaultdict(int)
    for r in submitted:
        if r["seconds_taken"]:
            day_key = (r["submitted_at"] or r["started_at"]).strftime("%Y-%m-%d")
            daily_seconds[day_key] += r["seconds_taken"]

    activity = []
    month_start = now.replace(day=1)
    day = month_start
    while day.month == month_start.month and day <= now:
        key = day.strftime("%Y-%m-%d")
        activity.append({"date": key, "minutes": round(daily_seconds.get(key, 0) / 60, 1)})
        day += timedelta(days=1)

    # --- pseudo-rank ---
    points = sum(POINTS_PER_SOLVE.get(r["difficulty"], 10) for r in solved)

    return {
        "total_solved": total_solved,
        "total_attempted": total_attempted,
        "accuracy_percent": accuracy,
        "avg_seconds_to_solve": avg_seconds,
        "by_difficulty": dict(by_difficulty),
        "growth": growth,
        "activity": activity,
        "rank_label": _rank_for_points(points),
        "rank_points": points,
    }
