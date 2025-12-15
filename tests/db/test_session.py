from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base, User
from app.db.session import get_engine, get_session, get_session_factory

SQLITE_URL = "sqlite:///:memory:"


@pytest.mark.skip("logic changed, will fix soon")
def test_get_session() -> None:
    mock_session = MagicMock()
    with patch("app.db.session.SessionLocal", return_value=mock_session):
        with get_session(mock_session):
            pass

    mock_session.begin.assert_called_once()
    mock_session.close.assert_called_once()


@pytest.mark.skip("logic changed, will fix soon")
def test_get_session_rollback_on_exception() -> None:
    mock_session = MagicMock()
    with patch("app.db.session.SessionLocal", return_value=mock_session):
        try:
            with get_session(mock_session):
                raise TypeError
        except TypeError:
            pass
    mock_session.begin.assert_called_once()
    mock_session.close.assert_called_once()


@pytest.fixture(scope="session")
def engine():
    return get_engine(SQLITE_URL)


@pytest.fixture(scope="session")
def session_maker(engine) -> sessionmaker[Session]:
    return get_session_factory(engine)


@pytest.fixture(scope="session")
def create_db(engine):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_user_creation(engine, create_db, session_maker):
    """
    Docstring for test_user_creation

    :param engine: Description
    :type engine: Engine
    :param create_db: Description
    :type create_db: None
    :param session_maker: Description
    :type session_maker: sessionmaker[Session]
    Rows are tuples.
    scalars() removes the tuple and keeps the first item.
    """
    user: User = User(name="test_name", username="test_username")
    user.password = "secret123"
    with get_session(session_maker) as test_session:
        test_session.add(user)
        stmt = Select(User.username).where(User.name == "test_name")
        result = test_session.execute(stmt).scalar_one()
        # assert result.name == "test_name"
        # assert result.username == "test_username"
        assert result == "test_username"
