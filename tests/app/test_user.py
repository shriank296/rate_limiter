def test_user_create(test_client, create_db):
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
    )

    assert response.status_code == 201, response.json()

    data = response.json()
    assert data["name"] == "Ankur"
    assert data["username"] == "shriank"
