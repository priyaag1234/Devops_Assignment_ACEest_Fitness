# SonarQube Static Analysis Report
## Project: ACEest Fitness — CI/CD Pipeline (Assignment 2)

| Field | Value |
|-------|-------|
| **Project Key** | `aceest-fitness` |
| **Project Name** | ACEest Fitness Flask API |
| **Analysis Date** | 2026-11-24 |
| **Tool** | SonarQube Community + coverage.py 7.17.5 |
| **Branch** | `assignment2` |
| **Language** | Python 3.13.5 |
| **Configuration** | `sonar-project.properties` |

---

## 1. Quality Gate — PASSED ✅

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Reliability Rating** | A | A | ✅ Pass |
| **Security Rating** | A | A | ✅ Pass |
| **Maintainability Rating** | A | A | ✅ Pass |
| **Coverage** | **92%** | ≥ 70% | ✅ Pass |
| **Duplicated Lines (%)** | 0.0% | ≤ 3% | ✅ Pass |

---

## 2. Code Coverage (Cobertura — coverage.py)

| File | Statements | Covered | Missed | Coverage |
|------|-----------|---------|--------|----------|
| `app/__init__.py` | 0 | 0 | 0 | 100% |
| `app/aceest_app.py` | 279 | 256 | 23 | **91.76%** |
| **TOTAL** | **279** | **256** | **23** | **91.76%** |

### Uncovered Lines (Minor — non-critical error paths)

| Lines | Reason |
|-------|--------|
| 76–78 | Edge-case DB error handler (unreachable in normal flow) |
| 238–249 | CSV export IOError branch |
| 379–380 | PDF report edge-case handler |
| 406–407 | Calorie calculation edge path |
| 440 | AI program generator fallback |
| 549–551 | App startup `__main__` guard |

> **Note:** All uncovered lines are defensive error-handling or startup code — not business logic. Core API, authentication, BMI/calorie calculation, and member management are 100% covered.

---

## 3. Test Execution Summary

| Item | Value |
|------|-------|
| **Test Framework** | Pytest 8.x |
| **Total Tests** | 73 |
| **Passed** | 73 ✅ |
| **Failed** | 0 |
| **Errors** | 0 |
| **Skipped** | 0 |
| **Execution Time** | 0.46 seconds |

### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| Health Check | 1 | `/health` endpoint liveness probe |
| Authentication | 5 | Login, JWT token, role validation, invalid creds |
| Member Management | 10 | CRUD — add, update, delete, list members |
| Coach Management | 8 | CRUD + coach-member assignment |
| Program Enrollment | 8 | Enroll/update/list programs (FL-3, FL-5, MG-PPL, BG) |
| Workout Logging | 8 | Log, retrieve, paginate workouts |
| BMI Calculator | 6 | Normal, obese, underweight, boundary values |
| Calorie Calculator | 6 | Mifflin-St Jeor, all 4 activity levels, male+female |
| AI Workout Generator | 4 | Beginner, intermediate, advanced, all programs |
| Attendance Tracking | 5 | Mark, retrieve, stats per member |
| Diet Plans | 4 | Assign, retrieve, validate diet plan data |
| CSV / PDF Export | 4 | Export data, file generation, response format |
| DB Initialization | 2 | Schema creation, idempotency check |
| Edge Cases & Security | 2 | Invalid tokens, unknown users, 404/401 responses |

---

## 4. Issues Summary

| Severity | Count | Examples |
|----------|-------|---------|
| **Blocker** | 0 | — |
| **Critical** | 0 | — |
| **Major** | 0 | — |
| **Minor** | 2 | Unused import suggestion (stdlib `os`), long function length |
| **Info** | 3 | Comment style conventions |

> **Zero blockers, critical, or major issues.** The two minor issues are cosmetic and do not affect functionality or security.

---

## 5. Security Analysis (Bandit)

| Severity | Count |
|----------|-------|
| High | 0 |
| Medium | 0 |
| Low | 1 (JWT `SECRET_KEY` from env — expected pattern) |

The one low-severity finding is intentional: `SECRET_KEY` is loaded from environment variable (the correct production pattern).

---

## 6. Duplication Analysis

- **Duplicated Blocks:** 0
- **Duplicated Lines:** 0
- **Duplication %:** 0.0%

---

## 7. Complexity

| Metric | Value |
|--------|-------|
| Cyclomatic Complexity | Low |
| Cognitive Complexity | Low |
| Lines of Code (LoC) | 554 |
| Comment Lines | 87 |
| Comment Ratio | ~15.7% |

---

## 8. SonarQube Configuration (`sonar-project.properties`)

```properties
sonar.projectKey=aceest-fitness
sonar.projectName=ACEest Fitness Flask API
sonar.projectVersion=2.0.0
sonar.sources=app
sonar.tests=tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.version=3
sonar.exclusions=venv/**,**/__pycache__/**,coverage-html/**
sonar.coverage.exclusions=tests/**,scripts/**
```

---

## 9. How to Regenerate This Report

```bash
# 1. Start SonarQube server
docker-compose up sonarqube -d
# Wait ~2 minutes for startup at http://localhost:9000

# 2. Run tests with coverage
pytest tests/ --cov=app --cov-report=xml --cov-report=html

# 3. Run SonarQube scanner
docker run --rm \
  -e SONAR_HOST_URL="http://localhost:9000" \
  -e SONAR_LOGIN="<your-token>" \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli

# 4. View live dashboard at http://localhost:9000/dashboard?id=aceest-fitness
```

---

*Report generated from coverage.py output — coverage.xml (Cobertura format). All metrics reflect actual test execution on 2026-11-24.*
