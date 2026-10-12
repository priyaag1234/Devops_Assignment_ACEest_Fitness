# Technical Document 1: Application Development & Architecture

**Project:** ACEest Fitness & Gym Management System  
**Course:** Introduction to DEVOPS (Merged - CSIZG514 / SEZG514) (S1-26)  
**Institution:** BITS Pilani  
**Document Purpose:** Architectural design, baseline evolution, API specifications, database schema, and local development lifecycle.

---

## 1. Executive Summary & Objective

The **ACEest Fitness & Gym** application is a foundational cloud-native web application designed to transition gym and athletic performance operations from legacy desktop environments into a scalable, microservices-ready REST API.

The project strictly follows the BITS Pilani DevOps Assignment 1 requirements:
1. **Zero External Installation Stack:** Implemented using Python Flask and Python's native embedded `sqlite3` database engine. The entire application runs anywhere (macOS, Linux, Windows, Docker, BITS VM) without installing or configuring external database servers like PostgreSQL, MySQL, or Redis.
2. **Domain-Driven Modularization:** Incorporates all business rules, mathematical equations, facility specifications, and nutrition plans from the original desktop baseline scripts.
3. **Rigorous Quality Gate:** 100% test coverage using Pytest (25 test cases), automated PEP 8 linting via Flake8, and compilation checking via `py_compile`.

---

## 2. Architecture & Design Decisions

### 2.1 Technology Stack Rationale

| Component | Technology | Rationale & Advantage |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ / 3.13 | High standard library maturity, excellent tooling, universal container compatibility. |
| **Web Framework** | Flask (>=3.0.0) | Lightweight WSGI microframework; minimal overhead, rapid startup, zero boilerplate. |
| **Database Engine** | Embedded SQLite3 | Standard Python built-in library; zero server configuration, ACID-compliant, self-contained single-file storage (`aceest_fitness.db`). |
| **Testing Framework**| Pytest (>=8.0.0) | Intuitive fixture model, assertions, test isolation, and rapid execution speed (0.16s for 25 tests). |
| **Linter / QA** | Flake8 (>=7.0.0) | Enforces PEP 8 compliance, catches syntax flaws and unused imports before build phases. |

### 2.2 Architectural Diagram

```
+--------------------------------------------------------------------------------------------------+
|                                    APPLICATION ARCHITECTURE                                      |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|   +------------------------------------------------------------------------------------------+   |
|   |                              HTTP REST Client / Browser / cURL                           |   |
|   +------------------------------------------------------------------------------------------+   |
|                                                |                                                 |
|                                                v (JSON Payloads / HTTP Requests)                 |
|   +------------------------------------------------------------------------------------------+   |
|   |                       Flask Application Gateway (app.py : Port 5000)                     |   |
|   +------------------------------------------------------------------------------------------+   |
|      |                  |                    |                     |                     |       |
|      v                  v                    v                     v                     v       |
|  [ Auth Service ]  [ Program API ]   [ Client Manager ]   [ Workout & Metrics ]  [ Calculators ] |
|  - Login           - Catalog         - Registration       - Session Logging      - Calorie Factor|
|  - Registration    - AI Generator    - Membership Expiry  - Adherence History    - Mifflin-St J. |
|  - Role Management - Regional Diets  - CSV Exporter       - Exercise Details     - BMI & Risk    |
|      |                  |                    |                     |                     |       |
|      +------------------+--------------------+---------------------+---------------------+       |
|                                                |                                                 |
|                                                v (Python DB-API 2.0 Connection Pool)             |
|   +------------------------------------------------------------------------------------------+   |
|   |              Embedded SQLite Datastore Engine (aceest_fitness.db / in-memory)            |   |
|   |   Tables: [users]  [clients]  [progress]  [workouts]  [exercises]  [metrics]             |   |
|   +------------------------------------------------------------------------------------------+   |
+--------------------------------------------------------------------------------------------------+
```

---

## 3. Evolution from Baseline Desktop Versions to Flask REST API

The assignment provided baseline Python Tkinter desktop applications (`versions/v1` through `versions/v6`). The table below outlines how each desktop GUI component was re-architected into modular REST services:

| Desktop Baseline Version | Legacy Desktop Implementation | Cloud-Native Modular Flask Implementation |
| :--- | :--- | :--- |
| **Version 1** (`v1_desktop_ui.py`) | Hardcoded GUI dictionary; Facility text labels (150 capacity, 10,000 sq ft, break-even 250); Tamil Nadu diet labels. | `GET /api/facility`, `GET /api/programs`, `GET /api/programs/<key>`. Return structured JSON models with HTTP status codes. |
| **Version 2** (`v2_calorie_logic.py`)| Tkinter Scale adherence widget; Calorie multiplier factors (`weight * 22`, `35`, `26`). | Dynamic calculation engine in `POST /api/clients` and `POST /api/calculator/calories`. |
| **Version 3** (`v3_sqlite_crud.py`) | Local SQLite file with `clients` and `progress` tables. | Managed connection handlers (`get_db_connection()`) with automated schema migrations. |
| **Version 4** (`v4_full_features.py`)| Expanded SQLite schema: `workouts`, `exercises`, `metrics`; BMI category alerts. | Dedicated REST endpoints: `POST /api/workouts`, `POST /api/metrics`, `POST /api/calculator/bmi` with clinical risk notes. |
| **Version 5** (`v5_aceest_full_login_ai.py`)| Tkinter Modal Login window; Random AI workout generator; PDF report generation. | Role-Based Auth API (`POST /api/auth/login`), Algorithmic Routine Generator (`POST /api/programs/generate`), Structured Report API (`GET /api/clients/<name>/report`). |
| **Version 6** (`v6_csv_export_coach_notes.py`)| FileDialog CSV exporter; Coach notes Entry widget. | Native zero-dependency CSV streaming endpoint (`GET /api/export/clients.csv`) using Python's standard `csv` and `io.StringIO` modules. |

---

## 4. Relational Database Schema Design (SQLite)

The application utilizes an embedded SQLite relational schema containing 6 normalized tables:

```
+--------------------+        +--------------------+        +--------------------+
|       users        |        |      clients       |        |      progress      |
+--------------------+        +--------------------+        +--------------------+
| id (INTEGER PK)    |        | id (INTEGER PK)    |        | id (INTEGER PK)    |
| username (TEXT UNQ)|        | name (TEXT UNQ)    |        | client_name (TEXT) |
| password (TEXT)    |        | age (INTEGER)      |        | week (TEXT)        |
| role (TEXT)        |        | height (REAL)      |        | adherence (INT)    |
+--------------------+        | weight (REAL)      |        +--------------------+
                              | program (TEXT)     |
                              | calories (INTEGER) |        +--------------------+
                              | target_weight(REAL)|        |      metrics       |
                              | target_adherence(I)|        +--------------------+
                              | membership_status  |        | id (INTEGER PK)    |
                              | membership_end     |        | client_name (TEXT) |
                              | notes (TEXT)       |        | date (TEXT)        |
+--------------------+        +--------------------+        | weight (REAL)      |
|      workouts      |                  |                   | waist (REAL)       |
+--------------------+                  |                   | bodyfat (REAL)     |
| id (INTEGER PK)    |<-----------------+                   +--------------------+
| client_name (TEXT) |
| date (TEXT)        |
| workout_type (TEXT)|        +--------------------+
| duration_min (INT) |        |     exercises      |
| notes (TEXT)       |        +--------------------+
+--------------------+        | id (INTEGER PK)    |
         |                    | workout_id (INT FK)|
         +------------------->| name (TEXT)        |
                              | sets (INTEGER)     |
                              | reps (INTEGER)     |
                              | weight (REAL)      |
                              +--------------------+
```

### Table Definitions:
1. `users`: Stores user authentication credentials. Defaults to `admin`/`admin` (`Admin` role).
2. `clients`: Stores member profiles, physical attributes, assigned program, calculated caloric target, goal targets, and membership expiry.
3. `progress`: Logs weekly gym adherence scores (0–100%).
4. `workouts`: Logs workout sessions (Strength, Hypertrophy, Conditioning, Mobility).
5. `exercises`: Stores individual exercise sets, reps, and resistance weight linked to a `workout_id`.
6. `metrics`: Tracks chronological body composition metrics (weight, waist, body fat percentage).

---

## 5. Complete REST API Specifications

### 5.1 System & Facility Endpoints
- **`GET /`**
  - **Purpose:** API discovery, metadata, and service directory.
  - **Response (200 OK):**
    ```json
    {
      "status": "online",
      "message": "Welcome to ACEest Fitness & Gym Management API",
      "version": "1.0.0",
      "facility_metrics": {
        "capacity": 150,
        "area_sq_ft": 10000,
        "break_even_members": 250
      }
    }
    ```
- **`GET /health`**
  - **Purpose:** Health-check probe for container orchestration and uptime monitoring.
  - **Response (200 OK):** `{"status": "healthy", "service": "ACEest Fitness & Gym API", "version": "1.0.0"}`
- **`GET /api/facility`**
  - **Purpose:** Returns gym facility specifications.

### 5.2 Authentication Endpoints
- **`POST /api/auth/login`**
  - **Payload:** `{"username": "admin", "password": "admin"}`
  - **Response (200 OK):** `{"success": true, "user": {"username": "admin", "role": "Admin"}}`
  - **Response (401 Unauthorized):** `{"success": false, "error": "Invalid username or password"}`
- **`POST /api/auth/register`**
  - **Payload:** `{"username": "coach_raj", "password": "secure123", "role": "Coach"}`
  - **Response (201 Created):** `{"success": true, "message": "User 'coach_raj' registered"}`

### 5.3 Programs & AI Routine Generator
- **`GET /api/programs`**: Returns all 4 programs (Fat Loss, Fat Loss 5-day, Muscle Gain, Beginner) with Tamil Nadu diet plans and workout splits.
- **`GET /api/programs/<key>`**: Returns single program details.
- **`POST /api/programs/generate`**:
  - **Payload:** `{"experience_level": "intermediate", "focus": "Conditioning"}`
  - **Response (200 OK):**
    ```json
    {
      "success": true,
      "experience_level": "intermediate",
      "days_per_week": 4,
      "schedule": [
        {
          "day": "Monday",
          "exercises": [
            {"name": "Burpees", "sets": 3, "reps": 12},
            {"name": "Running", "sets": 4, "reps": 10}
          ]
        }
      ]
    }
    ```

### 5.4 Client Management & CSV Export
- **`GET /api/clients`**: List all registered clients.
- **`POST /api/clients`**:
  - **Payload:** `{"name": "Bruce Wayne", "age": 32, "weight": 95.0, "program": "Muscle Gain (MG)"}`
  - **Logic:** Automatically calculates `calories = int(weight * 35) = 3325`.
  - **Response (201 Created):** Returns the persisted client record.
- **`GET /api/clients/<name>`**: Returns client profile, total weeks logged, average adherence, and latest metrics.
- **`GET /api/clients/<name>/membership`**: Returns membership billing status and expiration date.
- **`GET /api/export/clients.csv`**: Streams a downloadable RFC 4180 CSV containing all client records.

### 5.5 Progress, Workouts & Metrics
- **`POST /api/progress`**: Logs adherence percentage (`0-100`).
- **`POST /api/workouts`**: Logs session date, type, duration, notes, and exercises array.
- **`POST /api/metrics`**: Logs weight, waist circumference, and bodyfat percentage.

### 5.6 Fitness Calculators
- **`POST /api/calculator/calories`**:
  - *Method A (Program Factor):* `{"weight_kg": 70, "program": "Fat Loss (FL)"}` -> `1540 kcal`.
  - *Method B (Mifflin-St Jeor):* `{"weight_kg": 75, "height_cm": 180, "age": 25, "gender": "male", "activity_level": "moderate"}` -> BMR & maintenance calories.
- **`POST /api/calculator/bmi`**:
  - `{"weight_kg": 70, "height_cm": 175}` -> `BMI: 22.86`, `Category: "Normal"`, `Risk: "Low risk if active and strong."`.

---

## 6. Unit Testing Strategy & Verification

The test suite (`tests/test_app.py`) utilizes **Pytest** with isolated test database fixtures (`test_aceest_fitness.db`):

### 6.1 Test Coverage (25 Test Cases)
1. `test_home_endpoint` — Validates root route structure and facility metrics.
2. `test_health_check` — Confirms health probe returns HTTP 200.
3. `test_facility_metrics` — Validates gym specs (capacity, area, break-even).
4. `test_auth_login_success` — Validates default admin credentials.
5. `test_auth_login_invalid` — Validates HTTP 401 on incorrect credentials.
6. `test_auth_register` — Validates new user registration.
7. `test_get_programs` — Validates catalog retrieval.
8. `test_get_program_by_key_success` — Tests key lookup (`Beginner (BG)`).
9. `test_get_program_by_id_success` — Tests numeric ID lookup.
10. `test_get_program_not_found` — Tests HTTP 404 for non-existent program.
11. `test_ai_program_generator` — Tests dynamic routine generation.
12. `test_save_and_get_client` — Tests client persistence and calorie math.
13. `test_check_membership` — Validates membership renewal status.
14. `test_client_report` — Validates structured report output.
15. `test_export_clients_csv` — Validates RFC 4180 CSV export stream.
16. `test_save_client_validation_error` — Validates HTTP 400 on invalid input.
17. `test_get_client_not_found` — Tests HTTP 404 for missing client.
18. `test_save_and_get_progress` — Tests weekly adherence tracking.
19. `test_save_progress_invalid_adherence` — Validates 0-100 range validation.
20. `test_log_and_get_workouts` — Validates multi-exercise workout logging.
21. `test_log_and_get_metrics` — Validates body composition tracking.
22. `test_calculator_calories_program_factor` — Tests baseline factor calculation.
23. `test_calculator_calories_mifflin_st_jeor` — Tests clinical BMR calculation.
24. `test_calculator_bmi_and_risk` — Tests BMI category and risk notes.
25. `test_404_error` — Tests application-wide custom 404 JSON handler.

### 6.2 Test Execution Command
```bash
pytest -v tests/
```
**Result:** `25 passed in 0.16s (100% pass rate)`.

---

## 7. Local Developer Workflow

### Step-by-Step Local Setup:
```bash
# 1. Navigate to workspace
cd /Users/agarwal/Documents/Bits_devoops_assignment_1

# 2. Create isolated virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify syntax
python3 -m py_compile app.py tests/test_app.py

# 5. Check PEP 8 code quality
flake8 app.py tests/

# 6. Execute test suite
pytest -v tests/

# 7. Start application server
python app.py
```
Application will be active and listening at `http://127.0.0.1:5000` (`0.0.0.0:5000`).
