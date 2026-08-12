"""
psycopg v3 connection pool — replaces the SQLAlchemy engine/session.

ARCHITECTURE:
  • One `ConnectionPool` is created at module level (closed) and opened
    during FastAPI's lifespan startup (app/main.py).
  • `get_db()` is a FastAPI dependency generator: it borrows one connection
    from the pool, yields it to the route handler, then commits on success
    or rolls back on any exception before returning the connection to the pool.
  • Every repository method receives this connection as `db` — identical
    call-site signature to the old `Session`, so service code is unchanged.

TRANSACTION MODEL:
  All SQL within a single HTTP request shares one connection (and therefore
  one transaction). The repository methods do NOT commit; only `get_db()`
  commits, once, after the entire handler succeeds. This gives us
  all-or-nothing semantics across multi-step service pipelines (e.g.
  create source → ingest videos → create teacher_profile) for free.
"""

from psycopg_pool import ConnectionPool

from app.core.config import settings

# Pool is intentionally created in the "closed" state here and opened
# during the FastAPI lifespan (see app/main.py).  This keeps module import
# side-effects minimal and lets the lifespan control the exact moment the
# first real DB connection is attempted.
pool: ConnectionPool = ConnectionPool(
    conninfo=settings.DATABASE_URL,
    min_size=1,
    max_size=10,
    open=False,          # opened explicitly in lifespan
)


def get_db():
    """
    FastAPI dependency: yields one psycopg Connection per request.

    Usage in an endpoint:
        db: psycopg.Connection = Depends(get_db)
    """
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
