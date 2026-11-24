# CI/CD Pipeline Implementation Report
## ACEest Fitness — DevOps Assignment 2

| | |
|---|---|
| **Student / Project** | ACEest Fitness Gym Management System |
| **Repository** | https://github.com/priyaag1234/Devops_Assignment_ACEest_Fitness |
| **Branch** | `assignment2` |
| **Date** | November 2026 |
| **Course** | Introduction to DevOps — CI/CD Pipeline Assignment |

---

## 1. CI/CD Architecture Overview

### 1.1 High-Level Pipeline Flow

```
Developer Push
     │
     ▼
┌─────────────────────────────────────────────────┐
│              GitHub (assignment2 branch)         │
│  9 versioned commits  ·  9 annotated tags        │
└──────────────────┬──────────────────────────────┘
                   │ webhook / poll
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
   Jenkins Pipeline    GitHub Actions
   (Jenkinsfile)       (.github/workflows/ci-cd.yml)
         │
         ├── Stage 1: Checkout
         ├── Stage 2: Lint (flake8 + pylint — parallel)
         ├── Stage 3: Pytest + Coverage (92%)
         ├── Stage 4: SonarQube Analysis
         ├── Stage 5: Quality Gate (blocks if < 70% coverage)
         ├── Stage 6: Docker Build (multi-stage)
         ├── Stage 7: Container Health Check
         ├── Stage 8: Trivy Security Scan
         ├── Stage 9: Docker Hub Push
         └── Stage 10: Kubernetes Deploy (rolling update)
                           │
                    auto-rollback
                    on any failure
                           │
                           ▼
              ┌────────────────────────┐
              │  Minikube / Kubernetes  │
              │  Namespace: aceest      │
              │  Replicas: 2           │
              │  Strategy: RollingUpdate│
              │  Port: 80 → 5000       │
              └────────────────────────┘
```

### 1.2 Tool Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| **Version Control** | Git + GitHub | Source code management, branch strategy |
| **Build Automation** | Jenkins | 10-stage declarative pipeline |
| **Testing** | Pytest + pytest-cov | 73 automated tests, 92% coverage |
| **Code Quality** | SonarQube + flake8 + pylint | Static analysis, quality gate enforcement |
| **Security** | Bandit + Trivy | Python SAST + container vulnerability scanning |
| **Containerisation** | Docker (multi-stage) | Lightweight, non-root production image |
| **Registry** | Docker Hub | Versioned image storage (`aceest-fitness:latest`) |
| **Orchestration** | Kubernetes / Minikube | Rolling update deployment, zero-downtime |
| **Supplementary CI** | GitHub Actions | Matrix testing (Python 3.10 + 3.11) |

### 1.3 Branching Strategy

```
main (Assignment 1 — untouched)
│   Aceestver-1.0.py ... Aceestver-3.2.4.py
│
└── assignment2 (Assignment 2 DevOps infra)
    ├── assignment2-v1-setup     ← DevOps config files
    ├── assignment2-v2-flask-api ← Flask REST API (18 endpoints)
    ├── assignment2-v3-tests     ← 73 Pytest test cases
    ├── assignment2-v4-docker    ← Dockerfile + docker-compose
    ├── assignment2-v5-jenkins   ← Jenkinsfile (10-stage)
    ├── assignment2-v6-sonar     ← SonarQube configuration
    ├── assignment2-v7-k8s       ← Kubernetes manifests
    ├── assignment2-v8-actions   ← GitHub Actions workflow
    └── assignment2-v9-docs      ← README + deployment scripts
```

### 1.4 Application Architecture

The Flask REST API (`app/aceest_app.py`) exposes 18 endpoints covering:
- **Authentication** — JWT-based login with role validation (Admin / Coach / Member)
- **Member & Coach Management** — Full CRUD operations
- **Program Enrollment** — Fat Loss (3-day, 5-day), Muscle Gain (PPL), Beginner
- **Health Tracking** — BMI calculator (WHO categories), Mifflin-St Jeor calorie calculator
- **Workout Logging & Attendance** — Log, paginate, retrieve
- **AI Workout Generator** — Rule-based program generation by fitness level
- **Reports** — CSV export, PDF report generation

Data is persisted in SQLite (Kubernetes: mounted via PersistentVolumeClaim).

---

## 2. Challenges Faced and Mitigation Strategies

### Challenge 1 — GUI to API Migration

**Problem:** Assignment 1 code used a Tkinter desktop GUI. Jenkins/Docker/Kubernetes pipelines require a headless, testable server application. Tkinter cannot run without a display (`$DISPLAY` environment), which makes CI entirely impossible.

**Mitigation:** The application was rewritten as a **Flask REST API** while preserving 100% of the business logic (BMI calculation, calorie formula, program factors, all 18 original features). All routes return JSON, making the app fully testable, containerisable, and deployable.

---

### Challenge 2 — Git Authentication for Automated Push

**Problem:** HTTPS-based `git push` to GitHub failed with `Authentication failed` because GitHub removed password-based authentication for CLI operations. Attempting to push via PAT (Personal Access Token) also ran into encoding issues.

**Mitigation:** Switched to **SSH-based authentication** (`git@github.com:priyaag1234/...git`). The SSH key (`~/.ssh/id_ed25519`) was already registered with the GitHub account, making all subsequent push operations seamless with zero manual credentials.

---

### Challenge 3 — Protecting Assignment 1 (main branch)

**Problem:** Assignment 2 DevOps infrastructure needed to be added to the same repository without touching any Assignment 1 files (`app.py`, version files, original tests).

**Mitigation:** Entire Assignment 2 work was done on a **dedicated `assignment2` branch**. The `main` branch was never checked out or modified. Git branch isolation ensures the two assignments coexist cleanly in one repo. The Jenkinsfile and GitHub Actions workflow are both configured to operate only on `assignment2`.

---

### Challenge 4 — Test Coverage for All Endpoints

**Problem:** Flask endpoints require a running app context. Standard unit tests cannot call endpoints without special setup. Early test attempts either missed endpoints or required a live server.

**Mitigation:** Used **Flask's built-in test client** (`app.test_client()`). Every test sets up a fresh in-memory SQLite database (`TESTING=True`, `DATABASE=:memory:`), runs the endpoint under test, and tears down after — giving true isolation, repeatability, and speed (all 73 tests complete in under 0.5 seconds).

---

### Challenge 5 — Zero-Downtime Deployment

**Problem:** A naive `kubectl apply` replaces all pods simultaneously, causing a brief service outage.

**Mitigation:** Kubernetes `deployment.yaml` uses **RollingUpdate** strategy:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0   # never kill old pod before new one is ready
    maxSurge: 1         # spin up one extra pod during transition
```
Combined with `readinessProbe` on `/health`, Kubernetes only routes traffic to pods that have passed their health check, guaranteeing zero downtime.

---

### Challenge 6 — Auto-Rollback on Pipeline Failure

**Problem:** A failed Docker build or bad deployment could leave the cluster in a broken state with no manual intervention planned.

**Mitigation:** The Jenkinsfile `post { failure { ... } }` block automatically runs `kubectl rollout undo deployment/aceest-fitness -n aceest` on any stage failure. The deploy script (`scripts/deploy.sh rollback`) also provides a manual one-command rollback for operators.

---

## 3. Key Automation Outcomes

### 3.1 Test Quality

| Metric | Result |
|--------|--------|
| Total test cases | **73** |
| Pass rate | **100%** (73/73) |
| Code coverage | **92%** (threshold: 70%) |
| Execution time | **0.46 seconds** |
| Quality gate | **PASSED** |

The 73 tests cover all 18 API endpoints, all role-based access rules, boundary values for BMI and calorie calculators, error responses (401, 404, 400), and database lifecycle operations.

### 3.2 Pipeline Performance

| Stage | Outcome |
|-------|---------|
| Lint (flake8 + pylint) | Zero errors; runs in parallel |
| Test + Coverage | 92% — well above 70% threshold |
| SonarQube Quality Gate | PASSED — 0 blockers, 0 critical issues |
| Docker Image | Multi-stage build; non-root user `aceest`; HEALTHCHECK configured |
| Security Scan (Trivy) | No critical/high CVEs in production image |
| Kubernetes Deploy | Rolling update — 0 downtime; auto-rollback on failure |
| GitHub Actions Matrix | Passes on Python 3.10 and 3.11 |

### 3.3 DevOps Principles Demonstrated

| Principle | Implementation |
|-----------|---------------|
| **Continuous Integration** | Every push triggers lint + test + quality gate automatically |
| **Continuous Delivery** | Passing builds auto-push Docker image to registry |
| **Infrastructure as Code** | All K8s config in YAML (`k8s/`); Docker + Compose for local env |
| **Version Control** | 9 semantically tagged commits (`assignment2-v1` → `assignment2-v9`) |
| **Shift-Left Testing** | Pytest runs before Docker build — bugs caught early |
| **Security Scanning** | Bandit (Python SAST) + Trivy (container CVE scan) in pipeline |
| **Progressive Deployment** | Rolling update with `maxUnavailable: 0` = zero-downtime |
| **Rollback Capability** | `kubectl rollout undo` wired into Jenkins failure handler |
| **Observability** | `/health` liveness endpoint; `readinessProbe` for traffic gating |
| **Collaboration** | GitHub Actions provides PR-level CI for collaborative workflows |

### 3.4 Project Structure Summary

```
Devops_assignment2/
├── app/
│   └── aceest_app.py       Flask REST API — 18 endpoints, 554 LoC
├── tests/
│   └── test_aceest.py      73 Pytest tests — 92% coverage
├── Dockerfile              Multi-stage, non-root, HEALTHCHECK
├── docker-compose.yml      App + Jenkins + SonarQube + Postgres
├── Jenkinsfile             10-stage declarative pipeline
├── sonar-project.properties  SonarQube scanner config
├── k8s/
│   ├── namespace.yaml      Namespace: aceest
│   ├── deployment.yaml     RollingUpdate, 2 replicas, probes
│   ├── service.yaml        NodePort 80 → 5000
│   ├── pvc.yaml            1Gi SQLite persistence
│   └── configmap.yaml      Environment configuration
├── .github/workflows/
│   └── ci-cd.yml           4-job GitHub Actions pipeline
├── reports/
│   ├── sonarqube_analysis_report.md
│   └── CICD_Assignment_Report.md  ← this file
├── scripts/
│   ├── deploy.sh           Deploy / rollback / status helper
│   └── git_setup.sh        Version tagging automation
└── README.md               Full setup and usage documentation
```

---

## 4. Conclusion

This assignment successfully demonstrates an **end-to-end automated DevOps pipeline** for the ACEest Fitness gym management application. The pipeline enforces code quality at every stage — from linting and coverage-enforced unit testing through SonarQube static analysis to container security scanning — before progressively deploying to Kubernetes with built-in zero-downtime and auto-rollback guarantees.

The key takeaway is that DevOps is not a single tool but a **culture and set of practices**: by combining Git branching strategy, automated testing, quality gates, containerisation, and orchestration, teams can deliver software faster, with higher confidence, and with far less manual intervention.

---

*ACEest Fitness | DevOps Assignment 2 | November 2026*
*GitHub: https://github.com/priyaag1234/Devops_Assignment_ACEest_Fitness/tree/assignment2*
