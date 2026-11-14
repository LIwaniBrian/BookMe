
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Welcome to BookMe API",
        "status": "running",
    }


def test_application_title():
    assert app.title == "BookMe"


def test_application_version():
    assert app.version == "1.0.0"
