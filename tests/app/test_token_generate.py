import pytest

from app.security import JwtService
from tests.conftest import UserFactory


@pytest.fixture
def token_service():
    return JwtService(algorithm="HS256", secret="myprivatesecret")


def test_token_generate_for_user(create_db, test_client, token_service):
    user = UserFactory.create(password="secret")
    response = test_client.post(
        "/generate_token", data={"username": user.username, "password": "secret"}
    )
    assert response.status_code == 200, response.json()
    token = response.json()
    payload = token_service.decode(token)
    assert payload["sub"] == user.username


def test_token_invalid_password(create_db, test_client):
    user = UserFactory.create(password="secret")
    response = test_client.post(
        "/generate_token", data={"username": str(user.username), "password": "wrong"}
    )
    assert response.status_code == 401
