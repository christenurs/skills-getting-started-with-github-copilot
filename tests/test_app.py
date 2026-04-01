import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the activities state before each test to ensure isolation."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index():
    response = client.get("/")
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == len(activities)


def test_get_activities_contains_expected_keys():
    response = client.get("/activities")
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new@mergington.edu"},
    )
    assert response.status_code == 200
    assert "new@mergington.edu" in response.json()["message"]
    assert "new@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_unknown_activity_returns_404():
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "new@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_returns_400():
    # michael is already enrolled in Chess Club
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_unknown_activity_returns_404():
    response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up_returns_404():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "notregistered@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"
