"""
Unit Test Suite for ACEest Fitness & Gym Flask Application
BITS Pilani Introduction to DevOps Assignment 1
"""

import json
import os
import pytest

# Ensure testing uses an isolated test database
os.environ["DB_PATH"] = "test_aceest_fitness.db"

from app import app, init_db, PROGRAMS  # noqa: E402


@pytest.fixture(autouse=True)
def setup_test_db():
    """Reset the test database before each test run."""
    init_db()
    yield
    if os.path.exists("test_aceest_fitness.db"):
        try:
            os.remove("test_aceest_fitness.db")
        except OSError:
            pass


@pytest.fixture
def client():
    """Create Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- Core Info & Facility Tests ---

def test_home_endpoint(client):
    """Test the root endpoint returns welcome info and facility metrics."""
    response = client.get("/")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "online"
    assert "ACEest Fitness" in data["message"]
    assert "facility_metrics" in data
    assert data["facility_metrics"]["capacity"] == 150


def test_health_check(client):
    """Test health check probe."""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert data["service"] == "ACEest Fitness & Gym API"


def test_facility_metrics(client):
    """Test facility metrics endpoint returns baseline specifications."""
    response = client.get("/api/facility")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["data"]["area_sq_ft"] == 10000
    assert data["data"]["break_even_members"] == 250


# --- Authentication Tests ---

def test_auth_login_success(client):
    """Test admin default login succeeds."""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["success"] is True
    assert data["user"]["role"] == "Admin"


def test_auth_login_invalid(client):
    """Test login with wrong password fails with 401."""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert res.status_code == 401


def test_auth_register(client):
    """Test registering a new coach user."""
    res = client.post("/api/auth/register", json={"username": "coach_mike", "password": "pass123", "role": "Coach"})
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data["success"] is True


# --- Programs Catalog & AI Routine Generator Tests ---

def test_get_programs(client):
    """Test listing all fitness programs."""
    response = client.get("/api/programs")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["count"] == len(PROGRAMS)
    assert data["count"] >= 4


def test_get_program_by_key_success(client):
    """Test retrieving program by key."""
    response = client.get("/api/programs/Beginner%20(BG)")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["data"]["calorie_factor"] == 26


def test_get_program_by_id_success(client):
    """Test retrieving program by ID."""
    response = client.get("/api/programs/1")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["data"]["id"] == 1


def test_get_program_not_found(client):
    """Test non-existent program returns 404."""
    response = client.get("/api/programs/NonExistentProgram")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data["success"] is False


def test_ai_program_generator(client):
    """Test AI-style workout generator returns schedule."""
    payload = {"experience_level": "intermediate", "focus": "Conditioning"}
    res = client.post("/api/programs/generate", json=payload)
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["success"] is True
    assert data["days_per_week"] == 4
    assert len(data["schedule"]) == 4


# --- Client Management Tests ---

def test_save_and_get_client(client):
    """Test saving a client with automatic calorie calculation and retrieval."""
    payload = {
        "name": "Bruce Wayne",
        "age": 32,
        "height": 188.0,
        "weight": 95.0,
        "program": "Muscle Gain (MG)",
        "target_weight": 98.0,
        "target_adherence": 90,
        "membership_status": "Active",
        "membership_end": "2027-01-01",
        "notes": "Focused on deadlifts"
    }
    response = client.post(
        "/api/clients",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["data"]["calories"] == 3325

    # Retrieve client
    get_res = client.get("/api/clients/Bruce%20Wayne")
    assert get_res.status_code == 200
    get_data = json.loads(get_res.data)
    assert get_data["data"]["client"]["name"] == "Bruce Wayne"
    assert get_data["data"]["client"]["calories"] == 3325


def test_check_membership(client):
    """Test checking membership status and renewal date."""
    payload = {"name": "Diana Prince", "program": "Beginner (BG)", "weight": 68.0}
    client.post("/api/clients", json=payload)

    res = client.get("/api/clients/Diana%20Prince/membership")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["membership_status"] == "Active"


def test_client_report(client):
    """Test client report generation."""
    payload = {"name": "Clark Kent", "program": "Muscle Gain (MG)", "weight": 105.0}
    client.post("/api/clients", json=payload)

    res = client.get("/api/clients/Clark%20Kent/report")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "ACEest Client Report" in data["report_title"]


def test_export_clients_csv(client):
    """Test exporting clients to CSV."""
    client.post("/api/clients", json={"name": "Barry Allen", "program": "Fat Loss (FL)", "weight": 72.0})
    res = client.get("/api/export/clients.csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    assert "Barry Allen" in res.data.decode("utf-8")


def test_save_client_validation_error(client):
    """Test validation when client name or invalid program is provided."""
    res1 = client.post("/api/clients", data=json.dumps({}), content_type="application/json")
    assert res1.status_code == 400

    res2 = client.post(
        "/api/clients",
        data=json.dumps({"name": "Clark", "program": "InvalidProg"}),
        content_type="application/json"
    )
    assert res2.status_code == 400


def test_get_client_not_found(client):
    """Test querying non-existent client returns 404."""
    response = client.get("/api/clients/NoSuchClient")
    assert response.status_code == 404


# --- Progress Logging Tests ---

def test_save_and_get_progress(client):
    """Test logging weekly adherence progress."""
    prog_payload = {
        "client_name": "Bruce Wayne",
        "week": "Week 42 - 2026",
        "adherence": 85
    }
    res = client.post("/api/progress", data=json.dumps(prog_payload), content_type="application/json")
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data["success"] is True

    get_res = client.get("/api/progress/Bruce%20Wayne")
    assert get_res.status_code == 200
    get_data = json.loads(get_res.data)
    assert get_data["count"] == 1
    assert get_data["data"][0]["adherence"] == 85


def test_save_progress_invalid_adherence(client):
    """Test progress fails if adherence is out of range 0-100."""
    res = client.post(
        "/api/progress",
        data=json.dumps({"client_name": "Bruce", "adherence": 150}),
        content_type="application/json"
    )
    assert res.status_code == 400


# --- Workouts & Metrics Tests ---

def test_log_and_get_workouts(client):
    """Test logging workout with exercises."""
    workout_payload = {
        "client_name": "Bruce Wayne",
        "workout_type": "Strength",
        "duration_min": 75,
        "notes": "Heavy squats",
        "exercises": [
            {"name": "Back Squat", "sets": 5, "reps": 5, "weight": 140.0}
        ]
    }
    res = client.post("/api/workouts", data=json.dumps(workout_payload), content_type="application/json")
    assert res.status_code == 201

    get_res = client.get("/api/workouts/Bruce%20Wayne")
    assert get_res.status_code == 200
    data = json.loads(get_res.data)
    assert data["count"] == 1
    assert data["data"][0]["workout_type"] == "Strength"


def test_log_and_get_metrics(client):
    """Test logging body metrics."""
    metrics_payload = {
        "client_name": "Bruce Wayne",
        "weight": 94.5,
        "waist": 82.0,
        "bodyfat": 11.5
    }
    res = client.post("/api/metrics", data=json.dumps(metrics_payload), content_type="application/json")
    assert res.status_code == 201

    get_res = client.get("/api/metrics/Bruce%20Wayne")
    assert get_res.status_code == 200
    data = json.loads(get_res.data)
    assert data["count"] == 1
    assert data["data"][0]["weight"] == 94.5


# --- Calculators Tests ---

def test_calculator_calories_program_factor(client):
    """Test calorie calculator using baseline program factor."""
    payload = {"weight_kg": 70, "program": "Fat Loss (FL)"}
    res = client.post("/api/calculator/calories", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["target_calories"] == 1540


def test_calculator_calories_mifflin_st_jeor(client):
    """Test calorie calculator using Mifflin-St Jeor formula."""
    payload = {
        "weight_kg": 75,
        "height_cm": 180,
        "age": 25,
        "gender": "male",
        "activity_level": "moderate"
    }
    res = client.post("/api/calculator/calories", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["maintenance_calories"] > 2000


def test_calculator_bmi_and_risk(client):
    """Test BMI calculator with classification and risk notes from baseline."""
    payload = {"weight_kg": 70.0, "height_cm": 175.0}
    res = client.post("/api/calculator/bmi", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["category"] == "Normal"
    assert "Low risk" in data["risk_note"]


# --- Error Handling ---

def test_404_error(client):
    """Test unknown endpoint returns 404 JSON."""
    res = client.get("/api/does_not_exist")
    assert res.status_code == 404
    data = json.loads(res.data)
    assert data["success"] is False
