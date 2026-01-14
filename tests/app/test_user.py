def test_user_create(test_client, create_db, auth_headers):
    """
    Verify successful user creation via the POST /users endpoint.

    This test ensures that:
    - A valid JSON request payload creates a new user
    - The endpoint responds with HTTP 201 Created
    - The response body contains the expected user data
    """
    response = test_client.post(
        "/users",
        json={
            "name": "Ankur",
            "username": "shriank",
            "password": "secret123",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201, response.json()

    data = response.json()
    assert data["name"] == "Ankur"
    assert data["username"] == "shriank"


def test_user_create_using_authenticated_client(authenticated_test_client, create_db):
    """
    Verify successful user creation via the POST /users endpoint using authenticated client.

    This test ensures that:
    - A valid JSON request payload creates a new user
    - The endpoint responds with HTTP 201 Created
    - The response body contains the expected user data
    - Authenticated client is used which bypasses the checking of valid token.
    """
    response = authenticated_test_client.post(
        "/users",
        json={
            "name": "Shreya",
            "username": "shrishreya",
            "password": "secret123",
        },
    )

    assert response.status_code == 201, response.json()

    data = response.json()
    assert data["name"] == "Shreya"
    assert data["username"] == "shrishreya"


def test_user_create_too_many_requests(authenticated_test_client, create_db):
    # First request should succeed
    response1 = authenticated_test_client.post(
        "/users",
        json={
            "name": "test user 1",
            "username": "test_user_1",
            "password": "secret123",
        },
    )
    assert response1.status_code == 201

    # Second request should exceed rate limit
    response2 = authenticated_test_client.post(
        "/users",
        json={
            "name": "test user 2",
            "username": "test_user_2",
            "password": "secret123",
        },
    )
    assert response2.status_code == 429
