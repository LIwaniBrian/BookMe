from app.models import User


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


def test_user_can_access_own_business(client):
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
        "/business/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["business_name"] == "Demo Barbershop"


def test_business_access_requires_authentication(client):
    response = client.get("/business/me")

    assert response.status_code == 401


def test_two_businesses_are_isolated(client):
    # Register the first business
    register_test_user(client)

    # Register a second, independent business
    second_registration = client.post(
        "/auth/register",
        json={
            "business_name": "Demo Salon",
            "full_name": "Second Owner",
            "email": "second@example.com",
            "password": "TestPassword123!",
        },
    )

    assert second_registration.status_code == 201

    # Log in as the second business owner
    login_response = client.post(
        "/auth/login",
        json={
            "email": "second@example.com",
            "password": "TestPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    # Retrieve the authenticated owner's business
    response = client.get(
        "/business/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["business_name"] == "Demo Salon"
    assert response.json()["business_id"] == 2


def test_owner_can_access_dashboard(client):
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
        "/owner/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "owner"


def test_employee_cannot_access_owner_dashboard(client, db_session):
    register_test_user(client)

    user = db_session.query(User).filter(
        User.email == "owner@example.com"
    ).first()

    user.role = "employee"
    db_session.commit()

    login_response = client.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "TestPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/owner/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_user_cannot_access_another_business(client):
    register_test_user(client)

    second_registration = client.post(
        "/auth/register",
        json={
            "business_name": "Demo Salon",
            "full_name": "Second Owner",
            "email": "second@example.com",
            "password": "TestPassword123!",
        },
    )

    assert second_registration.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "TestPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    # Attempt to retrieve another business by changing its ID
    response = client.get(
        "/business/me?business_id=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["business_id"] == 1
    assert response.json()["business_name"] == "Demo Barbershop"
