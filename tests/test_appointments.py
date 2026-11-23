from tests.date_helpers import get_future_monday


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


def create_test_appointment(client, headers):
    service_response = client.post(
        "/services/",
        headers=headers,
        json={
            "name": "Haircut",
            "description": "Standard haircut",
            "price": "150.00",
            "duration_minutes": 45,
        },
    )

    employee_response = client.post(
        "/employees/",
        headers=headers,
        json={
            "full_name": "John Employee",
            "job_title": "Barber",
        },
    )

    client.post(
        "/business-hours/",
        headers=headers,
        json={
            "day_of_week": 0,
            "open_time": "09:00:00",
            "close_time": "17:00:00",
        },
    )

    appointment_response = client.post(
        "/appointments/",
        headers=headers,
        json={
            "service_id": service_response.json()["id"],
            "employee_id": employee_response.json()["id"],
            "customer_name": "Test Customer",
            "start_time": get_future_monday().isoformat(),
        },
    )

    assert appointment_response.status_code == 201

    return appointment_response.json()


def test_owner_can_list_appointments(client):
    token = create_owner_and_get_token(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    create_test_appointment(client, headers)

    response = client.get(
        "/appointments/",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["customer_name"] == "Test Customer"


def test_owner_can_get_single_appointment(client):
    token = create_owner_and_get_token(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    appointment = create_test_appointment(client, headers)

    response = client.get(
        f"/appointments/{appointment['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == appointment["id"]
    assert response.json()["customer_name"] == "Test Customer"


def test_owner_can_cancel_appointment(client):
    token = create_owner_and_get_token(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    appointment = create_test_appointment(client, headers)

    response = client.patch(
        f"/appointments/{appointment['id']}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cannot_cancel_appointment_twice(client):
    token = create_owner_and_get_token(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    appointment = create_test_appointment(client, headers)

    first_response = client.patch(
        f"/appointments/{appointment['id']}/cancel",
        headers=headers,
    )

    second_response = client.patch(
        f"/appointments/{appointment['id']}/cancel",
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == (
        "Appointment is already cancelled"
    )


def test_business_cannot_access_another_business_appointment(client):
    first_token = create_owner_and_get_token(client)

    first_headers = {
        "Authorization": f"Bearer {first_token}"
    }

    appointment = create_test_appointment(client, first_headers)

    client.post(
        "/auth/register",
        json={
            "business_name": "Second Salon",
            "full_name": "Second Owner",
            "email": "second@example.com",
            "password": "TestPassword123!",
        },
    )

    second_login = client.post(
        "/auth/login",
        json={
            "email": "second@example.com",
            "password": "TestPassword123!",
        },
    )

    second_token = second_login.json()["access_token"]

    second_headers = {
        "Authorization": f"Bearer {second_token}"
    }

    response = client.get(
        f"/appointments/{appointment['id']}",
        headers=second_headers,
    )

    assert response.status_code == 404


def test_appointments_require_authentication(client):
    response = client.get("/appointments/")

    assert response.status_code == 401
