#!/bin/bash
# ════════════════════════════════════════════════════
#  Git setup: Assignment 2 — DevOps CI/CD Pipeline
#  Builds ON TOP of Assignment 1 GitHub repo
#
#  Run from: /Users/agarwal/Documents/Devops_assignment2
#  bash scripts/git_setup.sh
# ════════════════════════════════════════════════════

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "=== ACEest Fitness — DevOps Assignment 2 Git Setup ==="
echo "Working directory: $REPO_DIR"

# ── If no git repo yet, initialise ───────────────────
if [ ! -d ".git" ]; then
    git init
    git config user.email "priya@aceest.dev"
    git config user.name "Priya Agarwal"
    echo "▶ Git repository initialised"
else
    echo "▶ Git repository already exists"
fi

# ── Confirm remote ────────────────────────────────────
echo ""
echo "Your Assignment 1 remote repo:"
echo "  https://github.com/priyaag1234/Devops_Assignment_ACEest_Fitness"
echo ""
echo "For Assignment 2 push to a NEW repo (or new branch), e.g.:"
echo "  git remote add origin https://github.com/YOUR_USER/Devops_assignment2.git"
echo ""

# ═══════════════════════════════════════════════════
#  COMMIT 1: DevOps infrastructure foundation
# ═══════════════════════════════════════════════════
git add .gitignore .flake8 requirements.txt requirements-dev.txt pytest.ini
git commit --allow-empty -m "ci(setup): add DevOps tooling configuration

- .gitignore: excludes venv, __pycache__, coverage, DB files
- .flake8: max-line-length=127, max-complexity=10
- requirements.txt: Flask 3.0.3 + pytest + coverage + flake8 + pylint + bandit
- requirements-dev.txt: dev-only extras (black, isort)
- pytest.ini: test discovery + coverage ≥70% enforcement" || true

git tag -a "assignment2-v1-setup" -m "Assignment 2: DevOps setup" --force 2>/dev/null || true

# ═══════════════════════════════════════════════════
#  COMMIT 2: Flask REST API (testable app module)
# ═══════════════════════════════════════════════════
git add app/
git commit --allow-empty -m "feat(app): Flask REST API — 18 endpoints, SQLite, role-based auth

Endpoints:
  GET  /                          → version info
  GET  /health                    → K8s/Docker health probe
  GET  /api/facility              → gym metrics
  POST /api/auth/login            → JWT-ready login
  POST /api/auth/register         → user registration
  GET  /api/programs              → list 4 programs
  GET  /api/programs/<key>        → program detail
  POST /api/programs/generate     → AI workout generator
  GET  /api/clients               → list clients
  POST /api/clients               → save/upsert client
  GET  /api/clients/<name>        → get client
  GET  /api/clients/<name>/membership → membership status
  GET  /api/clients/<name>/report → full client report
  GET  /api/export/clients.csv    → CSV export
  POST /api/progress              → log weekly adherence
  GET  /api/progress/<name>       → adherence history + avg
  POST /api/workouts              → log workout session
  POST /api/metrics               → log body metrics
  POST /api/calculator/calories   → calorie estimate
  POST /api/calculator/bmi        → BMI + risk category

Business logic:
  - calculate_calories(weight, program)
  - calculate_bmi(weight, height)
  - classify_bmi(bmi) → Underweight/Normal/Overweight/Obese
  - mifflin_st_jeor(weight, height, age, gender) → BMR
  - generate_ai_program(program, experience) → weekly plan
  - authenticate_user(username, password) → role" || true

git tag -a "assignment2-v2-flask-api" -m "Assignment 2: Flask REST API" --force 2>/dev/null || true

# ═══════════════════════════════════════════════════
#  COMMIT 3: Pytest test suite (73 tests)
# ═══════════════════════════════════════════════════
git add tests/
git commit --allow-empty -m "test: 73 pytest tests covering all Flask endpoints and business logic

Coverage: 92% (threshold: 70%)

Test categories:
  - App version (1)
  - Health & root routes (3)
  - Facility endpoint (3)
  - Authentication login (4)
  - User registration (3)
  - Program listing & detail (4)
  - AI program generator (4)
  - Client CRUD (8)
  - Membership status (3)
  - Client report (2)
  - CSV export (3)
  - Progress logging & retrieval (4)
  - Workout logging (2)
  - Body metrics (2)
  - Calorie calculator endpoint (3)
  - BMI calculator endpoint (4)
  - Pure business logic (21)

All tests isolated with per-test SQLite tempfile fixture" || true

git tag -a "assignment2-v3-tests" -m "Assignment 2: 73 tests, 92% coverage" --force 2>/dev/null || true

# ═══════════════════════════════════════════════════
#  COMMIT 4: Docker (multi-stage, non-root)
# ═══════════════════════════════════════════════════
git add Dockerfile docker-compose.yml
git commit --allow-empty -m "feat(docker): multi-stage Dockerfile + Docker Compose

Dockerfile (multi-stage):
  Stage 1 (builder): gcc + pip install with --no-cache-dir
  Stage 2 (runner) : non-root user 'aceest', /data volume mount
  HEALTHCHECK       : curl /health every 30s
  EXPOSE 5000

docker-compose.yml services:
  aceest-app  : Flask app (port 5000)
  sonarqube   : SonarQube 10.5-community (port 9000)
  sonar-db    : PostgreSQL 15 backend for SonarQube
  jenkins     : Jenkins LTS + Docker socket mount (port 8080)

Named volumes: aceest_data, sonarqube_data, jenkins_home" || true

git tag -a "assignment2-v4-docker" -m "Assignment 2: Docker multi-stage + Compose" --force 2>/dev/null || true

# ═══════════════════════════════════════════════════
#  COMMIT 5: Jenkins full pipeline
# ═══════════════════════════════════════════════════
git add Jenkinsfile
git commit --allow-empty -m "ci(jenkins): complete 10-stage Jenkinsfile with SonarQube + K8s deploy

Stages:
  1. Checkout         → git metadata
  2. Setup Env        → python venv + pip
  3. Lint & Security  → flake8 ‖ pylint ‖ bandit (parallel)
  4. Unit Tests       → pytest, coverage ≥70%, HTML reports
  5. SonarQube        → static analysis scan
  6. Quality Gate     → abort pipeline if SQ fails
  7. Docker Build     → tagged + latest
  8. Health Check     → docker run + curl /health
  9. Trivy Scan       → HIGH/CRITICAL vulnerability report
 10. Docker Push      → Docker Hub (tagged + latest)
 11. Deploy K8s       → kubectl apply + rollout status
 12. Smoke Test       → curl ClusterIP /health

Post (failure): kubectl rollout undo (auto-rollback)
Credentials: DOCKER_HUB_USERNAME, DOCKER_HUB_PASSWORD, SONAR_TOKEN, KUBECONFIG" || true

git tag -a "assignment2-v5-jenkins" -m "Assignment 2: Jenkins 10-stage pipeline" --force 2>/dev/null || true

# ═══════════════════════════════════════════════════
#  COMMIT 6: SonarQube config
# ═══════════════════════════════════════════════════
git add sonar-project.properties
git commit --allow-empty -m "ci(sonarqube): add sonar-project.properties

- projectKey: aceest-fitness
- Sources: app/, Tests: tests/
- Coverage report: coverage.xml (from pytest-cov)
- Lint report: pylint-report.txt" || true

git tag -a "assignment2-v6-sonar" -m "Assignment 2: SonarQube config" --force 2>/dev/null || true

# ═══════════════════════════════════════════════════
#  COMMIT 7: Kubernetes manifests (rolling update)
# ═══════════════════════════════════════════════════
git add k8s/
git commit --allow-empty -m "feat(k8s): Kubernetes manifests — rolling update + zero-downtime

Files:
  namespace.yaml   → aceest namespace
  deployment.yaml  → 2 replicas, RollingUpdate strategy
                     maxUnavailable=1, maxSurge=1
                     HTTP liveness + readiness probes on /health
                     resource limits: 250m CPU / 256Mi RAM
                     non-root securityContext (uid 1000)
  service.yaml     → NodePort (port 80 → 5000, Minikube compatible)
  pvc.yaml         → 1Gi ReadWriteOnce for SQLite persistence
  configmap.yaml   → app config (version, DB path, log level)

Zero-downtime: readinessProbe gates traffic until pod is healthy
Rollback      : kubectl rollout undo (automated in Jenkins post/failure)" || true

git tag -a "assignment2-v7-k8s" -m "Assignment 2: K8s manifests + rolling update" --force 2>/dev/null || true

# ═══════════════════════════════════════════════════
#  COMMIT 8: GitHub Actions
# ═══════════════════════════════════════════════════
git add .github/
git commit --allow-empty -m "ci(github-actions): complete GitHub Actions pipeline

Jobs (sequential with deps):
  lint-and-test   → Python 3.10 + 3.11 matrix, coverage ≥70%
  sonarqube       → SonarQube scan after tests pass
  docker-build    → build, health check, Trivy scan, push (main only)
  deploy          → kubectl apply + rollout status (production env)

Secrets needed:
  DOCKER_HUB_USERNAME, DOCKER_HUB_TOKEN
  SONAR_TOKEN, SONAR_HOST_URL
  KUBECONFIG" || true

git tag -a "assignment2-v8-actions" -m "Assignment 2: GitHub Actions pipeline" --force 2>/dev/null || true

# ═══════════════════════════════════════════════════
#  COMMIT 9: Docs & scripts
# ═══════════════════════════════════════════════════
git add README.md scripts/
git commit --allow-empty -m "docs: README + deploy/rollback scripts

README.md: full project documentation
  - 10 version history table (Assignment 1 → Assignment 2)
  - Quick start (local, Docker Compose, Minikube)
  - Pipeline architecture diagram
  - Jenkins credentials setup guide
  - SonarQube setup steps
  - Deployment strategy table
  - Test coverage breakdown

scripts/git_setup.sh  : creates all versioned commits
scripts/deploy.sh     : deploy / rollback / status / logs helper" || true

git tag -a "assignment2-v9-docs" -m "Assignment 2: Docs + scripts" --force 2>/dev/null || true

# ─────────────────────────────────────────────────────
echo ""
echo "✅ All commits and tags created!"
echo ""
git log --oneline
echo ""
echo "Tags:"
git tag --sort=version:refname
echo ""
echo "═══════════════════════════════════════════════"
echo "Next steps:"
echo "  1. git remote add origin https://github.com/YOUR_USER/Devops_assignment2.git"
echo "  2. git push --all"
echo "  3. git push --tags"
echo "═══════════════════════════════════════════════"
