from unittest.mock import MagicMock, patch

from sqlalchemy import Select

from app.db.models import User
from app.db.session import get_session
from tests.conftest import UserFactory


def test_get_session_happy_path() -> None:
    """
    get_session should:
    - create a Session from SessionLocal
    - start a transaction via session.begin()
    - yield the session
    - close the session when the generator is closed
    """
    mock_session = MagicMock()

    with patch("app.db.session.SessionLocal", return_value=mock_session):
        gen = get_session()

        # Act: enter the generator
        session = next(gen)

        # Assert: yielded session is the one created
        assert session is mock_session

        # Act: close generator (simulates request completion)
        gen.close()

        # Assert: transaction + cleanup happened
        mock_session.begin.assert_called_once()
        mock_session.close.assert_called_once()


def test_get_session_exception_path() -> None:
    """
    If an exception is thrown into the generator:
    - it should propagate
    - the session must still be closed
    """
    mock_session = MagicMock()

    with patch("app.db.session.SessionLocal", return_value=mock_session):
        gen = get_session()
        next(gen)  # enter generator

        try:
            gen.throw(ValueError("boom"))
        except ValueError:
            pass

        mock_session.close.assert_called_once()


def test_user_creation(engine, create_db, get_session_test) -> None:
    """
    Verify that a User can be:
    - persisted using the test session
    - queried back correctly

    Notes:
    - SQLAlchemy Core Select returns Row objects
    - scalar_one() extracts the single selected column value
    """
    user = User(name="test_name", username="test_username")
    user.password = "secret123"

    get_session_test.add(user)

    stmt = Select(User.username).where(User.name == "test_name")
    result = get_session_test.execute(stmt).scalar_one()

    assert result == "test_username"


def test_user_creation_using_factory(engine, create_db, get_session_test) -> None:
    """
    Verify UserFactory creates a persisted User
    and the stored data matches the factory output.
    """
    user = UserFactory.create(password="secret")

    stmt = Select(User).where(User.id == user.id)
    result = get_session_test.execute(stmt).one()

    # `.one()` returns a Row; iterate to access mapped entities
    for obj in result:
        assert obj.name == user.name
        assert obj.username == user.username
