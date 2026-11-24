# ACEest Fitness & Performance — DevOps CI/CD Pipeline

> **Assignment 2** — End-to-end automated DevOps pipeline built on the
> ACEest Fitness application developed in Assignment 1.

---

## Project Overview

**ACEest Fitness** is a gym management desktop application.
This repository demonstrates a complete **DevOps CI/CD pipeline** including:
version control, automated testing, code quality, containerisation,
container registry push, and Kubernetes deployment with rollback.

---

## Application Versions (Git Tags)

| Tag | File | Key Feature Added |
|-----|------|-------------------|
| `v1.0` | `Aceestver-1.0.py` | Basic tkinter UI – program display cards |
| `v1.1` | `Aceestver-1.1.py` | Client profile + calorie calculator |
| `v1.1.2` | `Aceestver1.1.2.py` | Multi-client table + CSV export |
| `v2.0.1` | `Aceestver2.0.1.py` | SQLite persistence (save/load clients) |
| `v2.1.2` | `Aceestver-2.1.2.py` | Matplotlib adherence progress chart |
| `v2.2.1` | `Aceestver-2.2.1.py` | Workout & body metrics logging |
| `v2.2.4` | `Aceestver-2.2.4.py` | Goals, client dropdown, status bar, tabs |
| `v3.0.1` | `Aceestver-3.0.1.py` | Code refactor & docstrings |
| `v3.1.2` | `Aceestver-3.1.2.py` | Role-based login, AI program, PDF export |
| `v3.2.4` | `Aceestver-3.2.4.py` | Full feature set + DevOps-ready |

---

## Repository Structure

```
Devops_assignment2/
├── app/
│   ├── __init__.py
│   └── aceest_app.py          ← Core logic (headless, testable)
├── tests/
│   ├── __init__.py
│   └── test_aceest.py         ← 49 pytest tests (98% coverage)
├── k8s/
│   ├── namespace.yaml
│   ├── deployment.yaml        ← RollingUpdate, 2 replicas
│   ├── service.yaml           ← NodePort (Minikube)
│   ├── pvc.yaml               ← 1Gi SQLite persistence
│   └── configmap.yaml
├── scripts/
│   ├── git_setup.sh           ← Create all versioned commits
│   └── deploy.sh              ← Manual deploy / rollback
├── .github/
│   └── workflows/
│       └── ci-cd.yml          ← GitHub Actions pipeline
├── Dockerfile                 ← Multi-stage, non-root user
├── docker-compose.yml         ← app + sonarqube + jenkins
├── Jenkinsfile                ← Full Jenkins pipeline
├── sonar-project.properties   ← SonarQube configuration
├── pytest.ini                 ← Test & coverage settings
├── requirements.txt           ← Runtime dependencies
├── requirements-dev.txt       ← Dev/test dependencies
├── .flake8                    ← Linter configuration
└── .gitignore
```

---

## CI/CD Pipeline Flow

```
GitHub Push
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                    Jenkins Pipeline                      │
│                                                          │
│  1. Checkout        ← git checkout + commit info         │
│  2. Setup Env       ← python venv + pip install          │
│  3. Lint (parallel) ← flake8 + pylint + bandit          │
│  4. Run Tests       ← pytest + coverage (≥70%)          │
│  5. SonarQube       ← static analysis                   │
│  6. Quality Gate    ← pass/fail threshold check         │
│  7. Docker Build    ← multi-stage image                 │
│  8. Trivy Scan      ← container vulnerability scan      │
│  9. Docker Push     ← Docker Hub push                   │
│ 10. Deploy K8s      ← kubectl apply (rolling update)    │
│ 11. Smoke Test      ← exec pod version check            │
│ 12. Post: Rollback  ← auto rollback on failure          │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Run Tests Locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

pytest tests/ -v --cov=app --cov-report=html
# → 49 tests pass, 98% coverage
```

### 2. Run with Docker Compose (app + Jenkins + SonarQube)

```bash
docker-compose up -d

# Access:
#   Jenkins:   http://localhost:8080
#   SonarQube: http://localhost:9000  (admin / admin)
```

### 3. Deploy to Minikube

```bash
# Start Minikube
minikube start

# Apply all K8s manifests
kubectl apply -f k8s/ -n aceest

# Check status
kubectl get pods -n aceest
kubectl get svc -n aceest
```

### 4. Git Setup (versioned commits)

```bash
# Creates all 10 version commits + tags automatically
bash scripts/git_setup.sh

# Push to your GitHub repo
git remote add origin https://github.com/YOUR_USER/Devops_assignment2.git
git push --all
git push --tags
```

### 5. Rollback

```bash
# Manual rollback via script
bash scripts/deploy.sh rollback

# Or direct kubectl
kubectl rollout undo deployment/aceest-deployment -n aceest
```

---

## Jenkins Setup

1. Install Jenkins locally or use the Docker Compose service.
2. Install plugins: **Git**, **Pipeline**, **SonarQube Scanner**,
   **HTML Publisher**, **Kubernetes CLI**.
3. Add these **Credentials** in Jenkins:
   | ID | Type | Description |
   |----|------|-------------|
   | `DOCKER_HUB_USERNAME` | Secret text | Docker Hub username |
   | `DOCKER_HUB_PASSWORD` | Secret text | Docker Hub password/token |
   | `SONAR_TOKEN` | Secret text | SonarQube user token |
   | `KUBECONFIG` | Secret file | `~/.kube/config` |
4. Create a **Pipeline** job pointing to this repo — Jenkins auto-reads `Jenkinsfile`.

---

## SonarQube Setup

```bash
# Start SonarQube (included in docker-compose)
docker-compose up sonarqube -d

# Wait ~2 min, then open http://localhost:9000
# Login: admin / admin → change password
# Create project: aceest-fitness
# Generate token → store in Jenkins as SONAR_TOKEN
```

---

## Deployment Strategies

| Strategy | How | Config |
|----------|-----|--------|
| **Rolling Update** | Gradual pod replacement | `maxUnavailable: 1`, `maxSurge: 1` |
| **Zero-downtime** | Old pods serve traffic while new start | `readinessProbe` gates traffic |
| **Auto Rollback** | Jenkins `post { failure }` block | `kubectl rollout undo` |
| **Manual Rollback** | `deploy.sh rollback` | `kubectl rollout undo` |

---

## Tools Used

| Tool | Purpose |
|------|---------|
| **Git + GitHub** | Version control, 10 tagged versions |
| **Jenkins** | Build automation & pipeline orchestration |
| **Pytest** | Automated testing (49 tests, 98% coverage) |
| **SonarQube** | Code quality & static analysis |
| **Docker** | Containerisation (multi-stage build) |
| **Docker Hub** | Container registry |
| **Minikube/K8s** | Container orchestration & deployment |
| **GitHub Actions** | Alternative CI (`.github/workflows/ci-cd.yml`) |
| **Trivy** | Container security scanning |
| **Flake8/Pylint** | Python linting |
| **Bandit** | Python security linting |

---

## Test Coverage

```
Name                Stmts   Miss  Cover
---------------------------------------
app/aceest_app.py      98      2    98%
---------------------------------------
TOTAL                  98      2    98%

49 passed in 0.18s
```

**Test categories:**
- Calorie calculation (7 tests)
- BMI calculation & classification (9 tests)
- Client validation (5 tests)
- Save/Load client (7 tests)
- Progress & adherence (6 tests)
- Client listing (2 tests)
- Authentication (4 tests)
- Program metadata (4 tests)
- Database initialisation (2 tests)
- App version (1 test)
