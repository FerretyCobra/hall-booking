"""Database engine and session.

The SQLite tuning here is what makes the booking flow safe under concurrency:

* journal_mode=WAL + busy_timeout  -> concurrent readers don't block, and a
  second writer waits for the lock instead of erroring out immediately.
* BEGIN IMMEDIATE on every transaction -> the write lock is taken *before* we
  run the "is this slot free?" check, so a check-then-insert can't interleave
  with another request. This is the real guard against double-booking, since
  SQLite has no exclusion constraint for overlapping time ranges.
"""
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_conn, _record):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA busy_timeout=5000")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()
    # Hand transaction control to us so we can emit BEGIN IMMEDIATE below.
    dbapi_conn.isolation_level = None


@event.listens_for(engine, "begin")
def _begin_immediate(conn):
    conn.exec_driver_sql("BEGIN IMMEDIATE")


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def transaction(db):
    """Commit-or-rollback around a block. Works whether or not a transaction was
    already autobegun (e.g. by an auth-check query earlier in the request).
    The first statement inside still triggers BEGIN IMMEDIATE via the event above."""
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise
