from unittest.mock import MagicMock, patch

from app.db.session import get_session


def test_get_session() -> None:
    mock_session = MagicMock()
    with patch("app.db.session.SessionLocal", return_value=mock_session):
        with get_session():
            pass

    mock_session.begin.assert_called_once()
    mock_session.close.assert_called_once()


def test_get_session_rollback_on_exception() -> None:
    mock_session = MagicMock()
    with patch("app.db.session.SessionLocal", return_value=mock_session):
        try:
            with get_session():
                raise TypeError
        except TypeError:
            pass
    mock_session.begin.assert_called_once()
    mock_session.close.assert_called_once()
