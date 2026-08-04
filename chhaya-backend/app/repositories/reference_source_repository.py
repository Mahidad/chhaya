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


reference_source_repository = ReferenceSourceRepository()
video_repository = VideoRepository()
