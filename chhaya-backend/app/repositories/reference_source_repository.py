import psycopg
from psycopg.rows import dict_row

from app.models.reference_source import ReferenceSource, Video
from app.repositories.base import BaseRepository


class ReferenceSourceRepository(BaseRepository[ReferenceSource]):
    _table = "reference_sources"
    _model = ReferenceSource

    # ------------------------------------------------------------------ #
    #  Video attachment helper                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _attach_videos(db: psycopg.Connection, sources: list[ReferenceSource]) -> None:
        """
        Populate the `videos` list on each source in a single query.

        This replaces the SQLAlchemy `relationship` lazy-load: instead of
        N+1 implicit queries, we do one explicit query and distribute the
        results by source_id.
        """
        if not sources:
            return
        ids = [s.id for s in sources]
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM videos WHERE source_id = ANY(%s) ORDER BY order_index",
                (ids,),
            )
            rows = cur.fetchall()

        video_map: dict[str, list[Video]] = {}
        for row in rows:
            video_map.setdefault(row["source_id"], []).append(Video(**row))

        for source in sources:
            source.videos = video_map.get(source.id, [])

    # ------------------------------------------------------------------ #
    #  Scoped lookups                                                      #
    # ------------------------------------------------------------------ #

    def get_for_user(
        self, db: psycopg.Connection, *, source_id: str, user_id: str
    ) -> ReferenceSource | None:
        """
        Scoping every lookup by user_id here (not just in the route) means
        a bug in one route can't accidentally leak another student's data —
        the repository itself refuses to return rows that aren't yours.
        """
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM reference_sources WHERE id = %s AND user_id = %s",
                (source_id, user_id),
            )
            row = cur.fetchone()
        if row is None:
            return None
        source = ReferenceSource(**row)
        self._attach_videos(db, [source])
        return source

    def list_for_user(
        self, db: psycopg.Connection, *, user_id: str
    ) -> list[ReferenceSource]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM reference_sources WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            rows = cur.fetchall()
        sources = [ReferenceSource(**row) for row in rows]
        self._attach_videos(db, sources)
        return sources

    def find_existing_by_url(
        self, db: psycopg.Connection, *, user_id: str, url: str
    ) -> ReferenceSource | None:
        """Exact-URL duplicate check -- catches re-submitting the identical link."""
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM reference_sources WHERE user_id = %s AND url = %s LIMIT 1",
                (user_id, url),
            )
            row = cur.fetchone()
        return ReferenceSource(**row) if row else None


class VideoRepository(BaseRepository[Video]):
    _table = "videos"
    _model = Video

    def bulk_create(
        self, db: psycopg.Connection, *, videos: list[dict]
    ) -> list[Video]:
        import uuid

        results: list[Video] = []
        from psycopg.rows import dict_row

        for v in videos:
            data = self._wrap_json({"id": str(uuid.uuid4()), **v})
            cols = list(data.keys())
            sql = (
                f"INSERT INTO videos ({', '.join(cols)}) "
                f"VALUES ({', '.join(['%s'] * len(cols))}) "
                f"RETURNING *"
            )
            with db.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, [data[c] for c in cols])
                results.append(self._row_to_obj(cur.fetchone()))
        return results

    def find_existing_video_for_user(
        self, db: psycopg.Connection, *, user_id: str, youtube_video_id: str
    ) -> dict | None:
        """
        Broader duplicate check than URL matching: catches the SAME video
        re-submitted under a different URL format (youtu.be/xyz vs
        youtube.com/watch?v=xyz), or reached a second time via a playlist
        after being added individually the first time. Returns a plain
        dict (not a Video) since it joins in fields from reference_sources
        that don't belong on the Video dataclass.
        """
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT v.*, rs.title AS source_title, rs.id AS existing_source_id
                FROM videos v
                JOIN reference_sources rs ON v.source_id = rs.id
                WHERE rs.user_id = %s AND v.youtube_video_id = %s
                LIMIT 1
                """,
                (user_id, youtube_video_id),
            )
            return cur.fetchone()

    def list_for_source(self, db: psycopg.Connection, *, source_id: str) -> list[Video]:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM videos WHERE source_id = %s ORDER BY order_index",
                (source_id,),
            )
            return [Video(**row) for row in cur.fetchall()]


reference_source_repository = ReferenceSourceRepository()
video_repository = VideoRepository()