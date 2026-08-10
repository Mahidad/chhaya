

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
