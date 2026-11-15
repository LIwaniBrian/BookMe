def register_test_user(client):
    return client.post(
        "/auth/register",
        json={
            "business_name": "Demo Barbershop",
            "full_name": "Test Owner",
            "email": "owner@example.com",
            "password": "TestPassword123!",
        },
    )


def test_business_registration(client):
    response = register_test_user(client)

    assert response.status_code == 201
    assert response.json()["business_name"] == "Demo Barbershop"


def test_duplicate_email_registration(client):
    register_test_user(client)

    response = register_test_user(client)

    assert response.status_code == 409


def test_successful_login(client):
    register_test_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert "access_token" in response.json()


def test_login_with_incorrect_password(client):
    register_test_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_access_account_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_access_account_with_valid_token(client):
    register_test_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "TestPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "owner@example.com"
    assert response.json()["business_id"] == 1
