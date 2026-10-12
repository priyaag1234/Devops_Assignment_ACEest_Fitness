# Technical Document 2: DevOps, Docker & Jenkins Pipelines

**Project:** ACEest Fitness & Gym Management System  
**Course:** Introduction to DEVOPS (Merged - CSIZG514 / SEZG514) (S1-26)  
**Institution:** BITS Pilani  
**Document Purpose:** Containerization strategy, Docker optimization & security, GitHub Actions CI/CD automation, and Jenkins Pipeline execution on the BITS VM.

---

## 1. Executive Summary & Pipeline Strategy

The **ACEest Fitness & Gym** DevOps implementation enforces an automated, multi-tiered CI/CD lifecycle across three distinct runtime environments:

```
+--------------------------------------------------------------------------------------------------+
|                                    END-TO-END DEVOPS LIFECYCLE                                   |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|   1. LOCAL LAPTOP                                                                                |
|      - Python development (app.py)                                                               |
|      - Local unit test verification (pytest -v tests/)                                           |
|      - Git commit & push to GitHub (branch: main)                                                |
|                                         |                                                        |
|                                         v (git push origin main)                                 |
|                                                                                                  |
|   2. GITHUB CLOUD (CI/CD Quality Gate 1)                                                         |
|      - Trigger: Push / Pull Request                                                              |
|      - GitHub Actions (.github/workflows/main.yml):                                              |
|          Stage 1: Build & Lint (flake8, py_compile)                                              |
|          Stage 2: Unit Testing on runner                                                         |
|          Stage 3: Docker Image Assembly (docker build)                                           |
|          Stage 4: Automated Testing INSIDE Container (docker run --rm image pytest)             |
|                                         |                                                        |
|                                         v (git clone / pull on VM)                               |
|                                                                                                  |
|   3. BITS VM & JENKINS (CI/CD Quality Gate 2)                                                    |
|      - Environment: BITS Virtual Machine (Ubuntu Linux)                                          |
|      - Jenkins Pipeline (Jenkinsfile):                                                           |
|          Stage 1: Checkout SCM (GitHub repo)                                                     |
|          Stage 2: Build & Lint (venv, flake8, py_compile)                                         |
|          Stage 3: Unit Testing (pytest)                                                          |
|          Stage 4: Docker Image Assembly (docker build -t aceest-fitness:latest .)                |
|          Stage 5: Containerized Testing (docker run --rm aceest-fitness:latest pytest)           |
|                                                                                                  |
+--------------------------------------------------------------------------------------------------+
```

---

## 2. Docker Containerization Strategy

The containerization strategy adheres strictly to the official BITS Pilani evaluation benchmark:  
*"Docker Efficiency: Is the Dockerfile optimized for size and security."*

### 2.1 Optimization & Security Architectural Principles

| Metric / Requirement | Architectural Implementation | Technical Rationale |
| :--- | :--- | :--- |
| **Base Image** | `python:3.11-slim` | Reduces image footprint from ~1 GB (standard Python) to <180 MB. Strips out compilers, debug tools, and unnecessary binaries, dramatically shrinking attack surface. |
| **Security / Least Privilege** | Non-root user: `appuser:appgroup` | Containers should never run as root. A dedicated system user `appuser` with `/sbin/nologin` shell is created, preventing privilege escalation vulnerabilities. |
| **Layer Caching** | Ordered file copying | `requirements.txt` is copied and installed *before* copying application code. Code changes will not trigger dependency re-downloads. |
| **Ephemeral Cache Elimination** | `pip install --no-cache-dir` | Prevents pip from caching wheel files inside the layer, saving 30–50 MB of disk space. |
| **Bytecode Suppression** | `ENV PYTHONDONTWRITEBYTECODE=1` | Eliminates `.pyc` creation on disk, ensuring clean execution and immutability. |
| **Live Log Streaming** | `ENV PYTHONUNBUFFERED=1` | Ensures stdout and stderr stream directly to Docker logs without buffering delays. |
| **Health Monitoring** | Built-in `HEALTHCHECK` directive | Probes `http://localhost:5000/health` every 30s. Automatically detects unresponsive containers. |

---

### 2.2 Dockerfile Line-by-Line Breakdown

```dockerfile
# 1. Use official lightweight slim Python image
FROM python:3.11-slim

# 2. Configure runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# 3. Set standard application working directory
WORKDIR /app

# 4. Security: Create dedicated non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# 5. Layer Caching: Install dependencies first
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy application source, test suite, and configuration files
COPY . /app

# 7. Grant ownership of /app to the non-root user
RUN chown -R appuser:appgroup /app

# 8. Switch execution context to non-root user
USER appuser

# 9. Document exposed port
EXPOSE 5000

# 10. Container Healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# 11. Entrypoint execution command
CMD ["python", "app.py"]
```

---

### 2.3 The `.dockerignore` Specification

Prevents build context pollution by excluding development and cache files:

```text
.git
.gitignore
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
.github/
.vscode/
*.swp
Jenkinsfile
README.md
```

---

### 2.4 Container Lifecycle Commands (BITS VM or Local)

#### Build the Docker Image:
```bash
docker build -t aceest-fitness:latest .
```

#### Run Automated Tests Inside the Container (Assignment Requirement):
```bash
docker run --rm aceest-fitness:latest pytest -v tests/
```

#### Start the Container in Detached Mode:
```bash
docker run -d --name aceest-gym -p 5000:5000 aceest-fitness:latest
```

#### Verify Running Containers:
```bash
docker ps
```

#### Test Live Health & Service Response:
```bash
curl http://localhost:5000/health
curl http://localhost:5000/api/facility
```

#### Inspect Container Logs:
```bash
docker logs -f aceest-gym
```

#### Stop and Clean Up:
```bash
docker stop aceest-gym
docker rm aceest-gym
```

---

## 3. GitHub Actions CI/CD Pipeline

Location: [`.github/workflows/main.yml`](file:///Users/agarwal/Documents/Bits_devoops_assignment_1/.github/workflows/main.yml)

### 3.1 Pipeline Structure

The pipeline triggers automatically on every `push` and `pull_request` to ensure zero regression:

1. **Job 1: `build-and-lint`**
   - Sets up Python 3.11 with pip caching.
   - Installs dependencies from `requirements.txt`.
   - Runs `python -m py_compile` to catch syntax errors.
   - Executes `flake8` to enforce PEP 8 style standards.
2. **Job 2: `test-local`** (Depends on `build-and-lint`)
   - Runs Pytest unit suite on runner host environment: `pytest -v tests/`.
3. **Job 3: `docker-build-and-test`** (Depends on `test-local`)
   - Builds the Docker image: `docker build -t aceest-fitness:latest .`.
   - **Crucial Assignment Check:** Executes Pytest **inside the container**:  
     `docker run --rm aceest-fitness:latest pytest -v tests/`.
   - Starts temporary container, verifies `/health` returns HTTP 200 via `curl`, then terminates and cleans up.

---

## 4. Jenkins CI/CD Pipeline on BITS VM

Location: [`Jenkinsfile`](file:///Users/agarwal/Documents/Bits_devoops_assignment_1/Jenkinsfile)

### 4.1 Role of Jenkins in the Architecture
In the BITS Pilani evaluation model, Jenkins serves as the **secondary, controlled BUILD server**:
- Pulls source code directly from the student's public GitHub repository.
- Performs a clean, reproducible build in an isolated VM environment.
- Validates syntax, runs tests, and builds the container image.

---

### 4.2 Declarative `Jenkinsfile` Implementation

```groovy
pipeline {
    agent any

    environment {
        APP_IMAGE = "aceest-fitness:latest"
        PORT = "5000"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                echo 'Checking out latest source code from GitHub...'
                checkout scm
            }
        }

        stage('Build & Lint') {
            steps {
                echo 'Validating Python syntax and code quality...'
                sh '''
                    python3 -m venv venv || virtualenv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    python3 -m py_compile app.py tests/test_app.py
                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                '''
            }
        }

        stage('Unit Testing') {
            steps {
                echo 'Running Pytest test suite...'
                sh '''
                    . venv/bin/activate
                    pytest -v tests/
                '''
            }
        }

        stage('Docker Image Assembly') {
            steps {
                echo 'Building Docker container image...'
                sh '''
                    docker build -t ${APP_IMAGE} .
                '''
            }
        }

        stage('Containerized Testing') {
            steps {
                echo 'Executing Pytest inside the containerized environment...'
                sh '''
                    docker run --rm ${APP_IMAGE} pytest -v tests/
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution completed.'
            sh '''
                rm -rf venv || true
            '''
        }
        success {
            echo 'Jenkins BUILD and Quality Gate PASSED successfully!'
        }
        failure {
            echo 'Jenkins BUILD FAILED. Check console logs for errors.'
        }
    }
}
```

---

### 4.3 Step-by-Step Jenkins Configuration on BITS VM

#### Step 1: Access Jenkins
1. Open your browser and navigate to the Jenkins URL on the VM (typically `http://localhost:8080` or `http://<VM-IP>:8080`).
2. Log in using your BITS VM Jenkins credentials.

#### Step 2: Create a New Pipeline Job
1. On the Jenkins dashboard, click **New Item** (top left).
2. Enter the item name: `aceest-fitness-pipeline`.
3. Select **Pipeline** as the item type.
4. Click **OK**.

#### Step 3: Configure the Pipeline from Git SCM
1. In the job configuration page, scroll down to the **Pipeline** section.
2. In the **Definition** dropdown, select **Pipeline script from SCM**.
3. In the **SCM** dropdown, select **Git**.
4. In **Repository URL**, enter your public GitHub repository:
   ```text
   https://github.com/YOUR-USERNAME/aceest-fitness-devops.git
   ```
5. In **Credentials**, leave as `none` (the repository is public).
6. In **Branch Specifier**, enter:
   ```text
   */main
   ```
   *(Or `*/master` if your repository default branch is master).*
7. In **Script Path**, ensure it is set to:
   ```text
   Jenkinsfile
   ```
8. Click **Save**.

#### Step 4: Execute the Build
1. In the left navigation menu of the job, click **Build Now**.
2. A new build entry (e.g. `#1`) will appear under **Build History**.
3. Click on the build number → click **Console Output** to monitor logs in real-time.
4. Verify that all stages (**Checkout SCM**, **Build & Lint**, **Unit Testing**, **Docker Image Assembly**, **Containerized Testing**) display green checkmarks in the Stage View.

---

### 4.4 Troubleshooting Jenkins on the BITS VM

| Issue | Root Cause | Solution on BITS VM Terminal |
| :--- | :--- | :--- |
| `docker: permission denied while trying to connect to the Docker daemon socket` | The `jenkins` system user does not have permission to access `/var/run/docker.sock`. | Run on VM: `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins`. |
| `python3: command not found` or `venv` fails | Python3 or virtualenv package is missing on the VM. | Run on VM: `sudo apt update && sudo apt install -y python3 python3-pip python3-venv`. |
| `docker: command not found` | Docker engine is not installed or not in PATH for Jenkins. | Run on VM: `sudo apt install -y docker.io && sudo systemctl enable --now docker`. |
| Git checkout branch error (`Couldn't find any revision to build`) | Default branch mismatch (`main` vs `master`). | Ensure branch specifier in Jenkins matches the actual GitHub branch (`*/main`). |

---

## 5. Submission Evidence & Screenshot Checklist

According to the BITS Pilani evaluation rubric, capture the following screenshots as evidence for your submission document:

- [ ] **Screenshot 1: Local Pytest Results**
  - Run `pytest -v tests/` in terminal. Shows **25 passed** tests in green.
- [ ] **Screenshot 2: Docker Build & Verification**
  - Shows `docker build -t aceest-fitness:latest .` succeeded.
  - Shows `docker run -d --name aceest-gym -p 5000:5000 aceest-fitness:latest` running.
  - Shows `curl http://localhost:5000/health` returning `{"status": "healthy", ...}`.
- [ ] **Screenshot 3: Containerized Pytest Run**
  - Shows `docker run --rm aceest-fitness:latest pytest -v tests/` passing inside the container.
- [ ] **Screenshot 4: GitHub Actions Green Pipeline**
  - In your GitHub repository, open the **Actions** tab.
  - Shows green checkmarks for `build-and-lint`, `test-local`, and `docker-build-and-test`.
- [ ] **Screenshot 5: Jenkins Pipeline Stage View**
  - In Jenkins, shows the stage view with all stages green (**Checkout**, **Build & Lint**, **Unit Testing**, **Docker Image Assembly**, **Containerized Testing**).
- [ ] **Public GitHub Repository Link**
  - Format: `https://github.com/<YOUR-USERNAME>/aceest-fitness-devops`
