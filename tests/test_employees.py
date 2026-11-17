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


def test_owner_can_create_employee(client):
    token = create_owner_and_get_token(client)

    response = client.post(
        "/employees/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "John Employee",
            "email": "john@example.com",
            "phone": "0712345678",
            "job_title": "Barber",
        },
    )

    assert response.status_code == 201
    assert response.json()["full_name"] == "John Employee"
    assert response.json()["job_title"] == "Barber"
    assert response.json()["is_active"] is True


def test_owner_can_list_employees(client):
    token = create_owner_and_get_token(client)

    client.post(
        "/employees/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "John Employee",
            "job_title": "Barber",
        },
    )

    response = client.get(
        "/employees/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["full_name"] == "John Employee"


def test_owner_can_update_employee(client):
    token = create_owner_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/employees/",
        headers=headers,
        json={
            "full_name": "John Employee",
            "job_title": "Barber",
        },
    )

    employee_id = create_response.json()["id"]

    response = client.patch(
        f"/employees/{employee_id}",
        headers=headers,
        json={
            "full_name": "John Updated",
            "job_title": "Senior Barber",
        },
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "John Updated"
    assert response.json()["job_title"] == "Senior Barber"


def test_owner_can_deactivate_employee(client):
    token = create_owner_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/employees/",
        headers=headers,
        json={
            "full_name": "John Employee",
            "job_title": "Barber",
        },
    )

    employee_id = create_response.json()["id"]

    response = client.delete(
        f"/employees/{employee_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Employee deactivated successfully"

    list_response = client.get(
        "/employees/",
        headers=headers,
    )

    assert list_response.json()[0]["is_active"] is False


def test_employee_creation_requires_authentication(client):
    response = client.post(
        "/employees/",
        json={
            "full_name": "John Employee",
            "job_title": "Barber",
        },
    )

    assert response.status_code == 401


def test_business_cannot_update_another_business_employee(client):
    token1 = create_owner_and_get_token(client)

    headers1 = {"Authorization": f"Bearer {token1}"}

    employee_response = client.post(
        "/employees/",
        headers=headers1,
        json={
            "full_name": "John Employee",
            "job_title": "Barber",
        },
    )

    employee_id = employee_response.json()["id"]

    # Register a second business.
    client.post(
        "/auth/register",
        json={
            "business_name": "Second Barbershop",
            "full_name": "Second Owner",
            "email": "second@example.com",
            "password": "TestPassword123!",
        },
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "second@example.com",
            "password": "TestPassword123!",
        },
    )

    token2 = login.json()["access_token"]

    response = client.patch(
        f"/employees/{employee_id}",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "full_name": "Hacked Employee",
        },
    )

    assert response.status_code == 404
