import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


# ---------------------------------------------------------------------------
# Engine creation (runs ONCE at import time)
#
# create_engine() is executed when this module is imported. It creates:
#   - ONE Engine object for the entire application lifetime
#   - ONE connection pool (no actual DB connections yet; they are opened lazily)
#
# This engine is reused by all sessions created through SessionLocal.
# It is NOT recreated per request or per dependency call.
# ---------------------------------------------------------------------------
def get_engine(db_url: str) -> Engine:
    engine: Engine = create_engine(db_url)
    return engine


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# sessionmaker factory (runs ONCE at import time)
#
# sessionmaker() returns a factory that creates new Session objects.
# This is created only once and reused for every request.
#
# SessionLocal() will be called per request to create a lightweight Session.
# The Session will borrow a DB connection from the engine's pool only
# when the first query is executed (lazy connection checkout).
# ---------------------------------------------------------------------------
def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    SessionLocal: sessionmaker[Session] = sessionmaker(
        bind=engine,
        autoflush=True,
        autocommit=False,
        expire_on_commit=False,  # common for FastAPI, avoids automatic re-fetch after commit
    )
    return SessionLocal


# ---------------------------------------------------------------------------
# Dependency-style session generator
#
# FastAPI understands generator dependencies:
#   - Code BEFORE `yield` is executed before the endpoint runs (setup)
#   - The value yielded becomes the dependency value (the DB session)
#   - Code AFTER `yield` runs after the endpoint completes (teardown)
#
# The @contextmanager decorator allows this function to behave both as
# a Python context manager AND as a FastAPI-compatible generator dependency.
#
# How the transaction works:
#   with session.begin():
#       - Starts a new transaction
#       - If the block exits normally → COMMIT happens automatically
#       - If an exception escapes the block → ROLLBACK happens automatically
#
# After the generator resumes post-yield, FastAPI triggers the teardown
# section, which closes the session, returning the DB connection to the pool.
# ---------------------------------------------------------------------------
@contextmanager
def get_session(SessionLocal: callable) -> Generator[Session, Any]:
    # Create a new Session object (cheap). Engine/sessionmaker are NOT recreated.
    session = SessionLocal()
    try:
        # Begin a transaction:
        #   - commit on normal exit
        #   - rollback if exception propagates
        with session.begin():
            # Yield the session to the caller (e.g., FastAPI endpoint)
            yield session
    except Exception:
        # Any exception (DB or user logic) logged here.
        # The transaction was already rolled back by session.begin().
        logger.exception("A database exception occured")
        raise
    finally:
        # Always close the session:
        #   - Releases the DB connection back to the engine's pool
        #   - Avoids connection leaks
        session.close()
