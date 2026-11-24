"""
Pytest test suite for ACEest Fitness Flask REST API
Tests all 18 endpoints + pure business logic functions.
"""

import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from aceest_app import (
    app as flask_app,
    init_db,
    calculate_calories,
    calculate_bmi,
    classify_bmi,
    mifflin_st_jeor,
    authenticate_user,
    generate_ai_program,
    get_app_version,
    PROGRAMS,
    FACILITY,
)


# ──────────────────────────────────────────────────────────────────────────────
#  Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    db = str(tmp_path / "test.db")
    init_db(db)
    return db


@pytest.fixture
def client(tmp_path):
    """Flask test client wired to a fresh temporary database."""
    db = str(tmp_path / "flask_test.db")
    init_db(db)
    flask_app.config["TESTING"] = True

    import aceest_app as mod
    original = mod.DB_PATH
    mod.DB_PATH = db
    mod.app.config["TESTING"] = True

    with flask_app.test_client() as c:
        with flask_app.app_context():
            yield c

    mod.DB_PATH = original


# ──────────────────────────────────────────────────────────────────────────────
#  App version
# ──────────────────────────────────────────────────────────────────────────────

def test_app_version():
    assert get_app_version() == "3.2.4"


# ──────────────────────────────────────────────────────────────────────────────
#  Health & root routes
# ──────────────────────────────────────────────────────────────────────────────

def test_health_endpoint_status(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_health_endpoint_body(client):
    r = client.get("/health")
    data = r.get_json()
    assert data["status"] == "healthy"
    assert data["version"] == "3.2.4"


def test_root_endpoint(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.get_json()
    assert "ACEest" in data["app"]
    assert data["status"] == "running"


# ──────────────────────────────────────────────────────────────────────────────
#  Facility endpoint
# ──────────────────────────────────────────────────────────────────────────────

def test_facility_returns_200(client):
    r = client.get("/api/facility")
    assert r.status_code == 200


def test_facility_contains_capacity(client):
    r = client.get("/api/facility")
    data = r.get_json()
    assert "capacity" in data
    assert data["capacity"] == 150


def test_facility_contains_name(client):
    r = client.get("/api/facility")
    data = r.get_json()
    assert "ACEest" in data["name"]


# ──────────────────────────────────────────────────────────────────────────────
#  Auth — login
# ──────────────────────────────────────────────────────────────────────────────

def test_login_valid_admin(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["role"] == "Admin"


def test_login_invalid_password(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_login_missing_credentials(client):
    r = client.post("/api/auth/login", json={})
    assert r.status_code == 400


def test_login_unknown_user(client):
    r = client.post("/api/auth/login", json={"username": "ghost", "password": "pass"})
    assert r.status_code == 401


# ──────────────────────────────────────────────────────────────────────────────
#  Auth — register
# ──────────────────────────────────────────────────────────────────────────────

def test_register_new_user(client):
    r = client.post("/api/auth/register",
                    json={"username": "coach1", "password": "pass123", "role": "Coach"})
    assert r.status_code == 201


def test_register_duplicate_user(client):
    client.post("/api/auth/register", json={"username": "u1", "password": "p1"})
    r = client.post("/api/auth/register", json={"username": "u1", "password": "p2"})
    assert r.status_code == 409


def test_register_missing_username(client):
    r = client.post("/api/auth/register", json={"password": "p1"})
    assert r.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
#  Programs
# ──────────────────────────────────────────────────────────────────────────────

def test_list_programs_returns_200(client):
    r = client.get("/api/programs")
    assert r.status_code == 200


def test_list_programs_has_four_programs(client):
    r = client.get("/api/programs")
    assert len(r.get_json()) == 4


def test_get_program_valid(client):
    r = client.get("/api/programs/Beginner (BG)")
    assert r.status_code == 200
    data = r.get_json()
    assert "factor" in data
    assert "desc" in data


def test_get_program_invalid(client):
    r = client.get("/api/programs/NonExistent")
    assert r.status_code == 404


# ──────────────────────────────────────────────────────────────────────────────
#  AI Program Generator
# ──────────────────────────────────────────────────────────────────────────────

def test_generate_program_success(client):
    r = client.post("/api/programs/generate", json={
        "program": "Beginner (BG)", "experience": "beginner"
    })
    assert r.status_code == 200
    data = r.get_json()
    assert "plan" in data
    assert len(data["plan"]) > 0


def test_generate_program_has_required_keys(client):
    r = client.post("/api/programs/generate", json={
        "program": "Muscle Gain (MG) - PPL", "experience": "advanced"
    })
    plan = r.get_json()["plan"]
    for item in plan:
        assert "day" in item
        assert "exercise" in item
        assert "sets" in item
        assert "reps" in item


def test_generate_program_invalid_program(client):
    r = client.post("/api/programs/generate", json={
        "program": "NonExistent", "experience": "beginner"
    })
    assert r.status_code == 400


def test_generate_program_invalid_experience(client):
    r = client.post("/api/programs/generate", json={
        "program": "Beginner (BG)", "experience": "expert"
    })
    assert r.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
#  Client management
# ──────────────────────────────────────────────────────────────────────────────

def test_create_client_success(client):
    r = client.post("/api/clients", json={
        "name": "Priya", "age": 25, "height": 160.0,
        "weight": 60.0, "program": "Beginner (BG)"
    })
    assert r.status_code == 201
    data = r.get_json()
    assert "Priya" in data["message"]
    assert data["calories"] > 0


def test_create_client_missing_name(client):
    r = client.post("/api/clients", json={"age": 25})
    assert r.status_code == 400


def test_get_client_exists(client):
    client.post("/api/clients", json={"name": "Ravi", "weight": 75.0,
                                      "program": "Muscle Gain (MG) - PPL"})
    r = client.get("/api/clients/Ravi")
    assert r.status_code == 200
    assert r.get_json()["name"] == "Ravi"


def test_get_client_not_found(client):
    r = client.get("/api/clients/Ghost")
    assert r.status_code == 404


def test_list_clients_empty(client):
    r = client.get("/api/clients")
    assert r.status_code == 200
    assert r.get_json() == []


def test_list_clients_after_insert(client):
    client.post("/api/clients", json={"name": "Zara"})
    client.post("/api/clients", json={"name": "Arjun"})
    r = client.get("/api/clients")
    names = r.get_json()
    assert "Zara" in names
    assert "Arjun" in names


def test_client_upsert(client):
    client.post("/api/clients", json={"name": "Meena", "age": 28})
    client.post("/api/clients", json={"name": "Meena", "age": 29})
    r = client.get("/api/clients/Meena")
    assert r.get_json()["age"] == 29


# ──────────────────────────────────────────────────────────────────────────────
#  Membership
# ──────────────────────────────────────────────────────────────────────────────

def test_membership_client_not_found(client):
    r = client.get("/api/clients/Ghost/membership")
    assert r.status_code == 404


def test_membership_active(client):
    client.post("/api/clients", json={
        "name": "Kumar", "membership_expiry": "2099-12-31"
    })
    r = client.get("/api/clients/Kumar/membership")
    assert r.status_code == 200
    assert r.get_json()["status"] == "Active"


def test_membership_expired(client):
    client.post("/api/clients", json={
        "name": "OldMember", "membership_expiry": "2020-01-01"
    })
    r = client.get("/api/clients/OldMember/membership")
    assert r.get_json()["status"] == "Expired"


# ──────────────────────────────────────────────────────────────────────────────
#  Client report
# ──────────────────────────────────────────────────────────────────────────────

def test_client_report_not_found(client):
    r = client.get("/api/clients/Ghost/report")
    assert r.status_code == 404


def test_client_report_success(client):
    client.post("/api/clients", json={"name": "Priya"})
    r = client.get("/api/clients/Priya/report")
    assert r.status_code == 200
    data = r.get_json()
    assert "client" in data
    assert "avg_adherence" in data


# ──────────────────────────────────────────────────────────────────────────────
#  CSV export
# ──────────────────────────────────────────────────────────────────────────────

def test_csv_export_returns_200(client):
    r = client.get("/api/export/clients.csv")
    assert r.status_code == 200


def test_csv_export_content_type(client):
    r = client.get("/api/export/clients.csv")
    assert "text/csv" in r.content_type


def test_csv_export_contains_header(client):
    r = client.get("/api/export/clients.csv")
    assert b"name" in r.data


# ──────────────────────────────────────────────────────────────────────────────
#  Progress / Adherence
# ──────────────────────────────────────────────────────────────────────────────

def test_log_progress_success(client):
    r = client.post("/api/progress", json={"client_name": "Priya", "adherence": 85})
    assert r.status_code == 201


def test_log_progress_missing_fields(client):
    r = client.post("/api/progress", json={"client_name": "Priya"})
    assert r.status_code == 400


def test_get_progress_empty(client):
    r = client.get("/api/progress/Ghost")
    data = r.get_json()
    assert data["records"] == []
    assert data["avg_adherence"] == 0


def test_get_progress_with_data(client):
    client.post("/api/progress", json={"client_name": "Ravi", "adherence": 70})
    client.post("/api/progress", json={"client_name": "Ravi", "adherence": 90})
    r = client.get("/api/progress/Ravi")
    data = r.get_json()
    assert len(data["records"]) == 2
    assert data["avg_adherence"] == 80.0


# ──────────────────────────────────────────────────────────────────────────────
#  Workouts
# ──────────────────────────────────────────────────────────────────────────────

def test_log_workout_success(client):
    r = client.post("/api/workouts", json={
        "client_name": "Priya", "workout_type": "Strength", "duration_min": 60
    })
    assert r.status_code == 201


def test_log_workout_missing_fields(client):
    r = client.post("/api/workouts", json={"client_name": "Priya"})
    assert r.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
#  Metrics
# ──────────────────────────────────────────────────────────────────────────────

def test_log_metrics_success(client):
    r = client.post("/api/metrics", json={
        "client_name": "Ravi", "weight": 74.5, "waist": 82.0, "bodyfat": 18.5
    })
    assert r.status_code == 201


def test_log_metrics_missing_client(client):
    r = client.post("/api/metrics", json={"weight": 74.5})
    assert r.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
#  Calorie Calculator endpoint
# ──────────────────────────────────────────────────────────────────────────────

def test_calc_calories_endpoint_success(client):
    r = client.post("/api/calculator/calories", json={
        "weight": 70.0, "program": "Beginner (BG)"
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data["calories"] == 1820


def test_calc_calories_endpoint_bad_program(client):
    r = client.post("/api/calculator/calories", json={
        "weight": 70.0, "program": "Unknown"
    })
    assert r.status_code == 400


def test_calc_calories_zero_weight(client):
    r = client.post("/api/calculator/calories", json={
        "weight": 0, "program": "Beginner (BG)"
    })
    assert r.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
#  BMI Calculator endpoint
# ──────────────────────────────────────────────────────────────────────────────

def test_calc_bmi_endpoint_success(client):
    r = client.post("/api/calculator/bmi", json={"weight": 70.0, "height": 175.0})
    assert r.status_code == 200
    data = r.get_json()
    assert "bmi" in data
    assert "category" in data


def test_calc_bmi_normal_range(client):
    r = client.post("/api/calculator/bmi", json={"weight": 70.0, "height": 175.0})
    assert r.get_json()["category"] == "Normal"


def test_calc_bmi_obese(client):
    r = client.post("/api/calculator/bmi", json={"weight": 120.0, "height": 170.0})
    assert r.get_json()["category"] == "Obese"


def test_calc_bmi_zero_height(client):
    r = client.post("/api/calculator/bmi", json={"weight": 70.0, "height": 0})
    assert r.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
#  Pure business logic functions
# ──────────────────────────────────────────────────────────────────────────────

def test_calculate_calories_fat_loss():
    assert calculate_calories(70.0, "Fat Loss (FL) - 3 day") == 1540

def test_calculate_calories_muscle_gain():
    assert calculate_calories(80.0, "Muscle Gain (MG) - PPL") == 2800

def test_calculate_calories_beginner():
    assert calculate_calories(70.0, "Beginner (BG)") == 1820

def test_calculate_calories_zero_raises():
    with pytest.raises(ValueError):
        calculate_calories(0, "Beginner (BG)")

def test_calculate_calories_unknown_raises():
    with pytest.raises(ValueError):
        calculate_calories(70.0, "NonExistent")

def test_calculate_bmi_normal():
    bmi = calculate_bmi(70.0, 175.0)
    assert bmi == 22.9

def test_classify_bmi_underweight():
    assert classify_bmi(17.0)["category"] == "Underweight"

def test_classify_bmi_normal():
    assert classify_bmi(22.0)["category"] == "Normal"

def test_classify_bmi_overweight():
    assert classify_bmi(27.0)["category"] == "Overweight"

def test_classify_bmi_obese():
    assert classify_bmi(35.0)["category"] == "Obese"

def test_classify_bmi_has_risk():
    assert "risk" in classify_bmi(22.0)

def test_mifflin_male():
    bmr = mifflin_st_jeor(70.0, 175.0, 30, "male")
    assert bmr > 0

def test_mifflin_female():
    bmr = mifflin_st_jeor(60.0, 160.0, 25, "female")
    assert bmr > 0

def test_authenticate_valid(tmp_db):
    import aceest_app as mod
    orig = mod.DB_PATH
    mod.DB_PATH = tmp_db
    role = authenticate_user("admin", "admin", tmp_db)
    mod.DB_PATH = orig
    assert role == "Admin"

def test_authenticate_invalid(tmp_db):
    role = authenticate_user("admin", "wrong", tmp_db)
    assert role is None

def test_authenticate_unknown_user(tmp_db):
    role = authenticate_user("ghost", "pass", tmp_db)
    assert role is None

def test_generate_ai_program_beginner():
    plan = generate_ai_program("Beginner (BG)", "beginner")
    assert len(plan) > 0
    assert all("day" in p and "exercise" in p for p in plan)

def test_generate_ai_program_advanced():
    plan = generate_ai_program("Muscle Gain (MG) - PPL", "advanced")
    days = {p["day"] for p in plan}
    assert len(days) == 5

def test_all_programs_have_factor():
    for name, data in PROGRAMS.items():
        assert "factor" in data and data["factor"] > 0

def test_db_init_creates_tables(tmp_db):
    import sqlite3
    conn = sqlite3.connect(tmp_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    conn.close()
    expected = {"users", "clients", "progress", "workouts", "exercises", "metrics"}
    assert expected.issubset(tables)

def test_db_init_idempotent(tmp_db):
    init_db(tmp_db)
    init_db(tmp_db)  # should not raise
