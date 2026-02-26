import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities  # activities is a dict

# client instance shared across tests
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: preserve original state and restore after each test."""
    original = copy.deepcopy(activities)
    yield
    # Assert/cleanup: restore state so tests are isolated
    activities.clear()
    activities.update(original)


def test_get_root_redirects():
    # Arrange: nothing special
    # Act
    response = client.get("/")
    # Assert
    assert response.status_code in (200, 307, 308)
    # the default FastAPI redirect may return 200 or 307 depending on client
    assert "/static/index.html" in response.url.path


def test_get_activities_returns_all():
    # Arrange
    expected = activities
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_success():
    # Arrange
    name = next(iter(activities))
    email = "new@student.edu"
    url = f"/activities/{name}/signup?email={email}"
    # Act
    response = client.post(url)
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {name}"
    assert email in activities[name]["participants"]


def test_signup_already_signed():
    # Arrange
    name, details = next(iter(activities.items()))
    email = details["participants"][0]
    url = f"/activities/{name}/signup?email={email}"
    # Act
    response = client.post(url)
    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_nonexistent_activity():
    # Arrange
    url = "/activities/NoSuchActivity/signup?email=test@x.com"
    # Act
    response = client.post(url)
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_full_activity():
    # Arrange
    name = "Tiny Club"
    activities[name] = {
        "description": "",
        "schedule": "",
        "max_participants": 1,
        "participants": ["already@here"]
    }
    url = f"/activities/{name}/signup?email=new@x.com"
    # Act
    response = client.post(url)
    # Assert
    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


def test_unregister_success():
    # Arrange
    name, details = next(iter(activities.items()))
    email = details["participants"][0]
    url = f"/activities/{name}/unregister?email={email}"
    # Act
    response = client.delete(url)
    # Assert
    assert response.status_code == 200
    assert email not in activities[name]["participants"]


def test_unregister_not_registered():
    # Arrange
    name = next(iter(activities))
    url = f"/activities/{name}/unregister?email=ghost@x.com"
    # Act
    response = client.delete(url)
    # Assert
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"].lower()


def test_unregister_nonexistent_activity():
    # Arrange
    url = "/activities/NoActivity/unregister?email=test@x.com"
    # Act
    response = client.delete(url)
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
