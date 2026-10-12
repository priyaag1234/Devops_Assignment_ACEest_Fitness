# ACEest Fitness & Gym — Automated CI/CD Pipeline

[![ACEest Fitness CI/CD Pipeline](https://github.com/YOUR-USERNAME/aceest-fitness-devops/actions/workflows/main.yml/badge.svg)](https://github.com/YOUR-USERNAME/aceest-fitness-devops/actions)

> **Course:** Introduction to DEVOPS (Merged - CSIZG514/SEZG514) (S1-26)  
> **Institution:** BITS Pilani  
> **Assignment:** Assignment 1 — Implementing Automated CI/CD Pipelines for ACEest Fitness & Gym  

---

## 1. Project Overview & Architecture

**ACEest Fitness & Gym** is a lightweight, zero-external-database Flask REST API and management system, modularized from the baseline functional fitness desktop applications to meet the modern cloud-native deployment standards of BITS Pilani DevOps Assignment 1.

### Key Highlights
- **Zero External Dependencies / Portability:** Powered entirely by Python's native standard library and `sqlite3` database engine (`aceest_fitness.db`). Requires **no** external database servers (PostgreSQL, MySQL, Redis), ensuring it runs instantly anywhere: on laptops, VMs, and inside lightweight containers.
- **Dedicated Technical Documentation:**
  - [Technical Document 1: Application Development & Architecture](DEVELOPMENT_TECHNICAL_DOCUMENT.md)
  - [Technical Document 2: DevOps, Docker & Jenkins Pipelines](DOCKER_JENKINS_TECHNICAL_DOCUMENT.md)
- **Full Baseline Domain Integration:** Directly incorporates every feature and specification across all baseline code versions:
  - **Facility Metrics:** 150 User capacity, 10,000 sq ft area, 250 member break-even.
  - **Role-Based Authentication:** Multi-user authentication (Admin, Coach, Member) with default `admin` / `admin` credentials.
  - **Workout Programs:** Fat Loss (FL, 3-day and 5-day), Muscle Gain (MG - PPL), Beginner (BG).
  - **AI Routine Generator:** Algorithmic workout plan generator producing structured routines based on experience level (`beginner`, `intermediate`, `advanced`) and focus.
  - **Nutrition & Diet Plans:** Tamil Nadu regional athletic nutrition (Idli-Sambar, Millet Roti, High-protein meal targets).
  - **Calorie Estimation:** Dynamic calorie target calculation via program factors (`weight * factor`) and Mifflin-St Jeor formula.
  - **Client Profiles & Progress Tracking:** Weekly adherence logging (0-100%), workout history with exercise sets/reps/weight, and body metrics tracking (weight, waist, bodyfat).
  - **Membership Billing & Reports:** Membership renewal dates, CSV export, and client summary reports.
  - **BMI & Health Risk:** Body Mass Index calculation and medical risk notes.
- **Comprehensive Quality Gates:** 100% test coverage via Pytest (25 automated tests), static code analysis with Flake8, and syntax compilation checks.
- **Dual Pipeline Integration:** Fully automated CI/CD pipeline in **GitHub Actions** (`.github/workflows/main.yml`) and a declarative **Jenkins Pipeline** (`Jenkinsfile`) for dedicated build servers / VMs.

```
+---------------------------------------------------------------------------------------+
|                                    DEVOPS LIFECYCLE                                   |
+---------------------------------------------------------------------------------------+
|  Local Development (Laptop)                                                          |
|    - Develop modular Flask app (app.py) incorporating baseline logic                  |
|    - Unit test locally (pytest) & lint (flake8)                                       |
|    - Commit & push to GitHub repository                                               |
|                           |                                                           |
|                           v                                                           |
|  GitHub Repository & Actions CI/CD                                                    |
|    - Trigger: Push / Pull Request                                                     |
|    - Stage 1: Build & Lint (flake8, py_compile)                                       |
|    - Stage 2: Host Pytest execution                                                   |
|    - Stage 3: Docker Image Assembly                                                   |
|    - Stage 4: Automated Pytest run INSIDE container                                   |
|                           |                                                           |
|                           v                                                           |
|  BITS VM / Jenkins BUILD Gate                                                         |
|    - Pull latest code from GitHub                                                     |
|    - Clean build in controlled environment                                            |
|    - Quality gate & Docker container verification                                     |
+---------------------------------------------------------------------------------------+
```

---

## 2. API Endpoints Catalog

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API welcome banner and service directory |
| `GET` | `/health` | Application healthcheck probe |
| `GET` | `/api/facility` | Facility metrics (Capacity: 150, Area: 10,000 sq ft, Break-even: 250) |
| `POST` | `/api/auth/login` | User authentication (default: `admin`/`admin`) |
| `POST` | `/api/auth/register` | Register new user account (Admin/Coach/Member) |
| `GET` | `/api/programs` | List all available fitness and nutrition programs |
| `GET` | `/api/programs/<key>` | Retrieve details of a specific fitness program by key or ID |
| `POST` | `/api/programs/generate` | AI Workout Routine Generator based on experience level |
| `GET` | `/api/clients` | List registered gym clients |
| `POST` | `/api/clients` | Register/update client (automatically calculates daily calories) |
| `GET` | `/api/clients/<name>` | Retrieve client profile, adherence summary, and latest metrics |
| `GET` | `/api/clients/<name>/membership` | Check membership billing status & renewal date |
| `GET` | `/api/clients/<name>/report` | Generate structured client report |
| `POST` | `/api/progress` | Log weekly client adherence percentage (0-100%) |
| `GET` | `/api/progress/<name>` | Retrieve adherence history for a client |
| `POST` | `/api/workouts` | Log workout session and exercise details (sets, reps, weight) |
| `GET` | `/api/workouts/<name>` | Retrieve workout history for a client |
| `POST` | `/api/metrics` | Log client body metrics (weight, waist, bodyfat) |
| `GET` | `/api/metrics/<name>` | Retrieve body metrics history for a client |
| `GET` | `/api/export/clients.csv` | Export entire client database to CSV format |
| `POST` | `/api/calculator/calories` | Calculate target calories based on program factor or Mifflin-St Jeor |
| `POST` | `/api/calculator/bmi` | Calculate Body Mass Index (BMI) and health category with risk notes |

---

## 3. Local Setup & Execution Instructions

### Prerequisites
- Python 3.10+ (Python 3.11+ recommended)
- `pip` package manager
- `git`

### Step 1: Clone the Repository
```bash
git clone https://github.com/YOUR-USERNAME/aceest-fitness-devops.git
cd aceest-fitness-devops
```

### Step 2: Create and Activate Virtual Environment
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Run the Application Locally
```bash
python app.py
```
The application will start on `http://127.0.0.1:5000` (or `http://0.0.0.0:5000`).

### Step 5: Manual Verification via cURL

**Health Check:**
```bash
curl -X GET http://127.0.0.1:5000/health
```

**User Login:**
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

**Generate AI Workout Routine:**
```bash
curl -X POST http://127.0.0.1:5000/api/programs/generate \
  -H "Content-Type: application/json" \
  -d '{"experience_level": "intermediate", "focus": "Conditioning"}'
```

**Register a Client (Auto-Calculates Caloric Target):**
```bash
curl -X POST http://127.0.0.1:5000/api/clients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bruce Wayne",
    "age": 32,
    "height": 188.0,
    "weight": 95.0,
    "program": "Muscle Gain (MG)",
    "target_weight": 98.0,
    "target_adherence": 90
  }'
```

**Export Database to CSV:**
```bash
curl -X GET http://127.0.0.1:5000/api/export/clients.csv -o clients.csv
```

---

## 4. Running Tests Manually

The test suite is written using **Pytest** and covers all API endpoints, edge cases, input validation, and HTTP 404 error responses.

### Run Unit Tests
```bash
pytest -v tests/
```

### Run Flake8 Code Linting
```bash
flake8 app.py tests/
```

### Run Python Syntax Compilation Check
```bash
python3 -m py_compile app.py tests/test_app.py
```

---

## 5. Docker Containerization

The `Dockerfile` is optimized for **security** and **minimal image size**:
1. Base image: `python:3.11-slim` (eliminates unnecessary OS packages).
2. Runs as a non-privileged user (`appuser`), following container security best practices.
3. Implements layered caching (`requirements.txt` installed before copying application code).
4. Includes built-in `HEALTHCHECK` instruction.

### Build Docker Image
```bash
docker build -t aceest-fitness:latest .
```

### Run the Container
```bash
docker run -d --name aceest-gym -p 5000:5000 aceest-fitness:latest
```

### Verify Container Health
```bash
curl http://localhost:5000/health
```

### Run Pytest Inside the Container
To verify container stability directly:
```bash
docker run --rm aceest-fitness:latest pytest -v tests/
```

### Stop & Remove Container
```bash
docker stop aceest-gym
docker rm aceest-gym
```

---

## 6. GitHub Actions CI/CD Pipeline

The GitHub Actions workflow is located at `.github/workflows/main.yml`. It is triggered automatically on every `push` and `pull_request`.

### Pipeline Stages
1. **Build & Lint (`build-and-lint`):**
   - Sets up Python 3.11 runtime.
   - Installs dependencies from `requirements.txt`.
   - Runs `python -m py_compile` to catch syntax errors.
   - Executes `flake8` to enforce code quality.
2. **Host Unit Testing (`test-local`):**
   - Executes `pytest -v tests/` in the runner environment.
3. **Docker Image Assembly & Containerized Testing (`docker-build-and-test`):**
   - Assembles the Docker image: `docker build -t aceest-fitness:latest .`.
   - Executes Pytest **inside the container**: `docker run --rm aceest-fitness:latest pytest -v tests/`.
   - Runs a temporary container, asserts `/health` probe returns HTTP 200, and cleans up.

---

## 7. Jenkins BUILD & Quality Gate Integration

The project includes a declarative `Jenkinsfile` for execution on a build server (e.g., the BITS VM).

### Jenkins Pipeline Stages
1. **Checkout SCM:** Pulls the latest commit from the GitHub repository.
2. **Build & Lint:** Sets up a clean virtual environment, installs dependencies, and runs flake8 / py_compile.
3. **Unit Testing:** Runs the Pytest suite.
4. **Docker Image Assembly:** Builds the image `docker build -t aceest-fitness:latest .`.
5. **Containerized Testing:** Executes tests inside the container `docker run --rm aceest-fitness:latest pytest -v`.

---

## 8. Repository File Structure

```text
aceest-fitness-devops/
├── .github/
│   └── workflows/
│       └── main.yml           # GitHub Actions CI/CD workflow
├── tests/
│   └── test_app.py            # Comprehensive 25-test Pytest test suite
├── versions/                  # Baseline versions provided for the assignment
│   ├── v1_desktop_ui.py       # Version 1: Initial desktop UI & facility metrics
│   ├── v2_calorie_logic.py    # Version 2: Caloric factors & adherence slider
│   ├── v3_sqlite_crud.py      # Version 3: SQLite persistence (clients, progress)
│   ├── v4_full_features.py    # Version 4: Full schema (workouts, exercises, metrics)
│   ├── v5_aceest_full_login_ai.py # Version 5: Login, membership, AI generator
│   └── v6_csv_export_coach_notes.py # Version 6: Coach notes, CSV export, table view
├── .dockerignore              # Excludes development artifacts from Docker
├── .flake8                    # Flake8 linter configuration
├── .gitignore                 # Excludes virtual environments and temporary files
├── Dockerfile                 # Optimized, non-root Python 3.11-slim container spec
├── Jenkinsfile                # Declarative Jenkins CI/CD pipeline
├── README.md                  # Complete project documentation
├── app.py                     # Standalone Flask web application
├── pytest.ini                 # Pytest configuration
└── requirements.txt           # Python application dependencies
```

---

## 9. License & Authors
- Developed as part of BITS Pilani M.Tech / Post-Graduate DevOps curriculum.
- Author: Student / Junior DevOps Engineer.
