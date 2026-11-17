def create_owner_and_get_token(client):
    registration = client.post(
        "/auth/register",
        json={
            "business_name": "Demo Barbershop",
            "full_name": "Test Owner",
            "email": "owner@example.com",
            "password": "TestPassword123!",
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "TestPassword123!",
        },
    )

    return login.json()["access_token"]


def test_owner_can_create_service(client):
    token = create_owner_and_get_token(client)

    response = client.post(
        "/services/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Haircut",
            "description": "Standard haircut",
            "price": "150.00",
            "duration_minutes": 45,
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Haircut"
    assert response.json()["price"] == "150.00"
    assert response.json()["duration_minutes"] == 45


def test_owner_can_list_services(client):
    token = create_owner_and_get_token(client)

    client.post(
        "/services/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Haircut",
            "price": "150.00",
            "duration_minutes": 45,
        },
    )

    response = client.get(
        "/services/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Haircut"


def test_owner_can_update_service(client):
    token = create_owner_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/services/",
        headers=headers,
        json={
            "name": "Haircut",
            "price": "150.00",
            "duration_minutes": 45,
        },
    )

    service_id = create_response.json()["id"]

    response = client.patch(
        f"/services/{service_id}",
        headers=headers,
        json={
            "name": "Premium Haircut",
            "price": "200.00",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Premium Haircut"
    assert response.json()["price"] == "200.00"
    assert response.json()["duration_minutes"] == 45


def test_owner_can_deactivate_service(client):
    token = create_owner_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/services/",
        headers=headers,
        json={
            "name": "Haircut",
            "price": "150.00",
            "duration_minutes": 45,
        },
    )

    service_id = create_response.json()["id"]

    response = client.delete(
        f"/services/{service_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Service deactivated successfully"


def test_service_creation_requires_authentication(client):
    response = client.post(
        "/services/",
        json={
            "name": "Haircut",
            "price": "150.00",
            "duration_minutes": 45,
        },
    )

    assert response.status_code == 401


def test_business_cannot_update_another_business_service(client):
    first_token = create_owner_and_get_token(client)

    create_response = client.post(
        "/services/",
        headers={"Authorization": f"Bearer {first_token}"},
        json={
            "name": "Haircut",
            "price": "150.00",
            "duration_minutes": 45,
        },
    )

    service_id = create_response.json()["id"]

    second_registration = client.post(
        "/auth/register",
        json={
            "business_name": "Second Salon",
            "full_name": "Second Owner",
            "email": "second@example.com",
            "password": "TestPassword123!",
        },
    )

    assert second_registration.status_code == 201

    second_login = client.post(
        "/auth/login",
        json={
            "email": "second@example.com",
            "password": "TestPassword123!",
        },
    )

    second_token = second_login.json()["access_token"]

    response = client.patch(
        f"/services/{service_id}",
        headers={"Authorization": f"Bearer {second_token}"},
        json={"name": "Modified Service"},
    )

    assert response.status_code == 404


def test_service_rejects_invalid_price(client):
    token = create_owner_and_get_token(client)

    response = client.post(
        "/services/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Haircut",
            "price": "-50.00",
            "duration_minutes": 45,
        },
    )

    assert response.status_code == 422
