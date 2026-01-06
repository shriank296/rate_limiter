"""
Global pytest configuration for database-backed tests.

This file defines:
- A single SQLite test engine
- A shared SQLAlchemy session factory
- A transaction-scoped session fixture
- Database schema lifecycle
- Factory Boy integration
"""

from typing import Generator

import factory
import pytest
from factory.alchemy import SQLAlchemyModelFactory
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base, User
from app.db.session import get_session, session_scope
from app.main import app
from app.security import get_current_user

# ---------------------------------------------------------------------------
# Test database configuration
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///./test.db"
# Alternative (true in-memory DB, but more fragile with multiple connections):
# SQLITE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Ensures a single connection for SQLite
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=test_engine,
    autoflush=True,
    autocommit=False,
    expire_on_commit=False,  # Matches typical FastAPI behavior
)


def factory_session() -> Session:
    """
    Session factory used by Factory Boy.

    Each factory call gets its own session to avoid
    leaking state between tests.
    """
    return SessionLocal()


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def engine():
    """
    Provide the shared SQLAlchemy engine for the test session.
    """
    return test_engine


@pytest.fixture
def get_session_test():
    """
    Provide a transaction-scoped SQLAlchemy session for tests.

    Uses the same unit-of-work logic as production (`session_scope`),
    ensuring identical commit/rollback/cleanup behavior.
    """
    yield from session_scope(SessionLocal)


@pytest.fixture(scope="session", autouse=True)
def create_db(engine):
    """
    Create all database tables once per test session.

    Drops and recreates the schema to ensure a clean baseline.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Factory Boy setup
# ---------------------------------------------------------------------------


class UserFactory(SQLAlchemyModelFactory):
    """
    Factory for creating persisted User instances.
    """

    name = factory.Faker("name")
    username = factory.Faker("user_name")

    class Meta:
        model = User
        sqlalchemy_session_factory = factory_session
        sqlalchemy_session_persistence = None  # commit handled manually

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Custom creation hook to support password hashing.

        Password is intercepted and assigned via the model setter
        before committing the instance.
        """
        password = kwargs.pop("password", "secret")

        session = cls._meta.sqlalchemy_session_factory()
        obj = model_class(**kwargs)
        obj.password = password

        session.add(obj)
        session.commit()

        return obj


@pytest.fixture(scope="function")
def test_client(get_session_test) -> Generator[TestClient, None, None]:
    client = TestClient(app)

    def override_get_session():
        # get_session_test HERE is the actual Session object
        yield get_session_test

    client.app.dependency_overrides[get_session] = override_get_session

    yield client

    client.app.dependency_overrides.clear()


@pytest.fixture
def test_user(create_db, get_session_test) -> User:
    user = UserFactory.create(password="test_password")
    return user


@pytest.fixture
def auth_headers(test_user, test_client):
    response = test_client.post(
        "/generate_token",
        data={"username": test_user.username, "password": "test_password"},
    )
    access_token = response.json()
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def authenticated_test_client(
    get_session_test, test_user, test_client
) -> Generator[TestClient, None, None]:
    def override_get_current_user():
        # test_user here overrides the get_cuurent_user so auth part is never called
        yield test_user

    test_client.app.dependency_overrides[get_current_user] = override_get_current_user

    yield test_client

    test_client.app.dependency_overrides.clear()
