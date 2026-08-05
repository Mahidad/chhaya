"""
Analytics dataclasses — mirror the two new DB tables:
  - study_sessions   : one row per learning session a student opens
  - study_guide_views: one row each time a completed guide page is viewed

These are plain Python dataclasses (no ORM) — psycopg hydrates them via
the BaseRepository._row_to_obj helper which just does Model(**row_dict).
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class StudySession:
    id: str
    user_id: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_secs: int | None = None  # filled when session is closed
    is_seed: bool = False             # TRUE for rows inserted by the seed endpoint


@dataclass
class StudyGuideView:
    id: str
    user_id: str
    study_guide_id: str
    viewed_at: datetime
    is_seed: bool = False             # TRUE for rows inserted by the seed endpoint
