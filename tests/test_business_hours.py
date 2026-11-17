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


def test_owner_can_create_business_hours(client):
    token = create_owner_and_get_token(client)

    response = client.post(
        "/business-hours/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "day_of_week": 0,
            "open_time": "09:00:00",
            "close_time": "17:00:00",
            "is_closed": False,
        },
    )

    assert response.status_code == 201
    assert response.json()["day_of_week"] == 0
    assert response.json()["open_time"] == "09:00:00"
    assert response.json()["close_time"] == "17:00:00"


def test_owner_can_list_business_hours(client):
    token = create_owner_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

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
        "/business-hours/",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["day_of_week"] == 0


def test_owner_can_update_business_hours(client):
    token = create_owner_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/business-hours/",
        headers=headers,
        json={
            "day_of_week": 0,
            "open_time": "09:00:00",
            "close_time": "17:00:00",
        },
    )

    response = client.put(
        "/business-hours/0",
        headers=headers,
        json={
            "day_of_week": 0,
            "open_time": "08:00:00",
            "close_time": "18:00:00",
            "is_closed": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["open_time"] == "08:00:00"
    assert response.json()["close_time"] == "18:00:00"


def test_duplicate_business_hours_are_rejected(client):
    token = create_owner_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
        "day_of_week": 0,
        "open_time": "09:00:00",
        "close_time": "17:00:00",
    }

    first_response = client.post(
        "/business-hours/",
        headers=headers,
        json=data,
    )

    second_response = client.post(
        "/business-hours/",
        headers=headers,
        json=data,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 400


def test_business_hours_require_authentication(client):
    response = client.get("/business-hours/")

    assert response.status_code == 401


def test_business_cannot_access_another_business_hours(client):
    first_token = create_owner_and_get_token(client)

    first_headers = {
        "Authorization": f"Bearer {first_token}"
    }

    client.post(
        "/business-hours/",
        headers=first_headers,
        json={
            "day_of_week": 0,
            "open_time": "09:00:00",
            "close_time": "17:00:00",
        },
    )

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
        "/business-hours/",
        headers=second_headers,
    )

    assert response.status_code == 200
    assert response.json() == []

    update_response = client.put(
        "/business-hours/0",
        headers=second_headers,
        json={
            "day_of_week": 0,
            "open_time": "08:00:00",
            "close_time": "18:00:00",
        },
    )

    assert update_response.status_code == 404
