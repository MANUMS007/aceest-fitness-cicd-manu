"""
Pytest suite for the ACEest Fitness & Gym Flask application.

Run locally with:
    pytest -v

Covers:
    * Health check endpoint
    * Program catalogue endpoint
    * Client creation (happy path + validation errors)
    * Client retrieval / listing / deletion
    * Calorie calculation business logic
    * Weekly adherence/progress logging
"""

import pytest

from app import create_app, calculate_calories


@pytest.fixture
def client():
    """Provides a fresh Flask test client (and fresh in-memory store)
    for every single test function."""
    flask_app = create_app(testing=True)
    with flask_app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------
def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json()["status"] == "running"


# ---------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------
def test_list_programs(client):
    response = client.get("/programs")
    assert response.status_code == 200
    data = response.get_json()
    assert "Fat Loss (FL)" in data
    assert "Muscle Gain (MG)" in data
    assert "Beginner (BG)" in data


# ---------------------------------------------------------------------
# Calorie calculation (pure function)
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "weight, program, expected",
    [
        (70, "Fat Loss (FL)", 1540),
        (80, "Muscle Gain (MG)", 2800),
        (60, "Beginner (BG)", 1560),
    ],
)
def test_calculate_calories(weight, program, expected):
    assert calculate_calories(weight, program) == expected


# ---------------------------------------------------------------------
# Client creation
# ---------------------------------------------------------------------
def test_add_client_success(client):
    payload = {"name": "Arun", "age": 28, "weight": 70, "program": "Fat Loss (FL)"}
    response = client.post("/clients", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Arun"
    assert data["calories"] == 1540
    assert data["progress"] == []


def test_add_client_missing_name(client):
    payload = {"age": 28, "weight": 70, "program": "Fat Loss (FL)"}
    response = client.post("/clients", json=payload)
    assert response.status_code == 400
    assert "name" in response.get_json()["error"]


def test_add_client_invalid_program(client):
    payload = {"name": "Kavya", "age": 24, "weight": 55, "program": "Cardio Blast"}
    response = client.post("/clients", json=payload)
    assert response.status_code == 400
    assert "Invalid program" in response.get_json()["error"]


def test_add_client_invalid_weight(client):
    payload = {"name": "Deepak", "age": 30, "weight": -5, "program": "Beginner (BG)"}
    response = client.post("/clients", json=payload)
    assert response.status_code == 400


def test_add_duplicate_client(client):
    payload = {"name": "Arun", "age": 28, "weight": 70, "program": "Fat Loss (FL)"}
    client.post("/clients", json=payload)
    response = client.post("/clients", json=payload)
    assert response.status_code == 409


# ---------------------------------------------------------------------
# Client retrieval / listing / deletion
# ---------------------------------------------------------------------
def test_get_client_not_found(client):
    response = client.get("/clients/Ghost")
    assert response.status_code == 404


def test_list_clients_after_creation(client):
    client.post(
        "/clients",
        json={"name": "Priya", "age": 22, "weight": 58, "program": "Beginner (BG)"},
    )
    response = client.get("/clients")
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_delete_client(client):
    client.post(
        "/clients",
        json={"name": "Priya", "age": 22, "weight": 58, "program": "Beginner (BG)"},
    )
    response = client.delete("/clients/Priya")
    assert response.status_code == 200
    assert client.get("/clients/Priya").status_code == 404


# ---------------------------------------------------------------------
# Weekly adherence / progress
# ---------------------------------------------------------------------
def test_add_and_get_progress(client):
    client.post(
        "/clients",
        json={"name": "Rahul", "age": 26, "weight": 75, "program": "Muscle Gain (MG)"},
    )
    response = client.post(
        "/clients/Rahul/progress", json={"week": "Week 1", "adherence": 85}
    )
    assert response.status_code == 201

    response = client.get("/clients/Rahul/progress")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["adherence"] == 85


def test_add_progress_invalid_adherence(client):
    client.post(
        "/clients",
        json={"name": "Rahul", "age": 26, "weight": 75, "program": "Muscle Gain (MG)"},
    )
    response = client.post(
        "/clients/Rahul/progress", json={"week": "Week 1", "adherence": 150}
    )
    assert response.status_code == 400


def test_add_progress_client_not_found(client):
    response = client.post(
        "/clients/Ghost/progress", json={"week": "Week 1", "adherence": 50}
    )
    assert response.status_code == 404
