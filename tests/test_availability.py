from datetime import datetime

from tests.test_services import create_owner_and_get_token


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


def test_employee_is_available_during_business_hours(client):
    token = create_owner_and_get_token(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

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

    hours_response = client.post(
        "/business-hours/",
        headers=headers,
        json={
            "day_of_week": 0,
            "open_time": "09:00:00",
            "close_time": "17:00:00",
            "is_closed": False,
        },
    )

    assert service_response.status_code == 201
    assert employee_response.status_code == 201
    assert hours_response.status_code == 201

    response = client.get(
        "/availability/",
        headers=headers,
        params={
            "service_id": service_response.json()["id"],
            "employee_id": employee_response.json()["id"],
            "start_time": "2026-11-23T10:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["available"] is True


def test_appointment_outside_business_hours_is_unavailable(client):
    token = create_owner_and_get_token(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

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

    response = client.get(
        "/availability/",
        headers=headers,
        params={
            "service_id": service_response.json()["id"],
            "employee_id": employee_response.json()["id"],
            "start_time": "2026-11-23T16:30:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["reason"] == (
        "Appointment falls outside business hours"
    )


def test_appointment_on_closed_day_is_unavailable(client):
    token = create_owner_and_get_token(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

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
            "is_closed": True,
        },
    )

    response = client.get(
        "/availability/",
        headers=headers,
        params={
            "service_id": service_response.json()["id"],
            "employee_id": employee_response.json()["id"],
            "start_time": "2026-11-23T10:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["reason"] == (
        "Business is closed on this day"
    )


def test_employee_with_existing_appointment_is_unavailable(client):
    token = create_owner_and_get_token(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

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
            "start_time": "2026-11-23T10:00:00",
        },
    )

    assert appointment_response.status_code == 201

    response = client.get(
        "/availability/",
        headers=headers,
        params={
            "service_id": service_response.json()["id"],
            "employee_id": employee_response.json()["id"],
            "start_time": "2026-11-23T10:30:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["reason"] == (
        "Employee already has an appointment at this time"
    )
