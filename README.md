# ACEest Fitness & Gym — Automated CI/CD Pipeline

A Flask-based fitness & gym management service, built and delivered using a
full DevOps lifecycle: **Git → Pytest → Docker → Jenkins → GitHub Actions**.

This repository was produced for *Introduction to DevOps (CSIZG514/SEZG514)
— Assignment 1*, implementing automated CI/CD pipelines for ACEest Fitness
& Gym.

---

## 1. Project Structure

```
.
├── app.py                      # Flask application (core logic + REST API)
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # + pytest, flake8 (test/lint tooling)
├── pytest.ini                  # Pytest configuration
├── conftest.py                 # Ensures app.py is importable by tests
├── tests/
│   └── test_app.py             # Pytest unit test suite
├── Dockerfile                  # Container image definition
├── .dockerignore
├── .gitignore
├── Jenkinsfile                 # Jenkins BUILD & quality-gate pipeline
└── .github/
    └── workflows/
        └── main.yml             # GitHub Actions CI/CD pipeline
```

---

## 2. Application Overview

The app manages fitness clients enrolled in one of three programs, each
with its own calorie-estimation factor:

| Program            | Calorie Factor (kcal / kg body weight) |
|---------------------|-----------------------------------------|
| Fat Loss (FL)        | 22 |
| Muscle Gain (MG)     | 35 |
| Beginner (BG)        | 26 |

### API Endpoints

| Method | Endpoint                          | Description                          |
|--------|------------------------------------|---------------------------------------|
| GET    | `/`                                 | Health check                          |
| GET    | `/programs`                         | List all available programs           |
| GET    | `/clients`                          | List all clients                      |
| POST   | `/clients`                          | Create a client                       |
| GET    | `/clients/<name>`                   | Get a client's profile                |
| DELETE | `/clients/<name>`                   | Remove a client                       |
| POST   | `/clients/<name>/progress`          | Log a week's adherence %              |
| GET    | `/clients/<name>/progress`          | Get a client's adherence history      |

Example — create a client:

```bash
curl -X POST http://localhost:5000/clients \
     -H "Content-Type: application/json" \
     -d '{"name": "Arun", "age": 28, "weight": 70, "program": "Fat Loss (FL)"}'
```

---

## 3. Local Setup & Execution

### Prerequisites
- Python 3.12+
- Docker (optional, for containerized run)
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/MANUMS007/aceest-fitness-cicd-manu.git
cd <your-repo>

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Run the application locally
python app.py
# App is now available at http://localhost:5000
```

### Run with Docker

```bash
docker build -t aceest-fitness .
docker run -p 5000:5000 aceest-fitness
```

---

## 4. Running Tests Manually

The project uses **Pytest** to validate the internal logic of the Flask
application (client creation, validation rules, calorie calculation,
adherence tracking, and error handling).

```bash
# From the project root, with the virtual environment activated:
pytest -v
```

Expected output: all test cases in `tests/test_app.py` pass (health check,
program listing, calorie formula, client CRUD, and progress logging /
validation).

To run tests **inside the Docker container** (matching what CI does):

```bash
docker build -t aceest-fitness .
docker run --rm --entrypoint "" -v $(pwd):/workspace -w /workspace aceest-fitness \
    sh -c "pip install pytest && pytest -v"
```

---

## 5. CI/CD Pipeline Overview

### 5.1 GitHub Actions (`.github/workflows/main.yml`)

Triggered automatically on **every `push`** and **every `pull_request`**.
The pipeline runs three sequential jobs:

1. **Build & Lint** — compiles `app.py` (`py_compile`) and runs `flake8`
   to catch syntax/style errors early.
2. **Docker Image Assembly** — builds the Docker image, boots a
   container from it and curls the health-check endpoint to confirm the
   container actually starts and serves traffic (not just that it
   builds), then uploads the image as a build artifact.
3. **Automated Testing** — loads the built image and executes the full
   Pytest suite *inside* the containerized environment, so the tests
   validate the exact artifact that would be deployed — not just the
   local Python environment.

Each job depends on the previous one (`needs:`), so the pipeline fails
fast: if linting fails, the image is never built; if the image fails to
build, tests are never run against it.

### 5.2 Jenkins (`Jenkinsfile`)

Jenkins performs an **independent, secondary validation layer** — a
clean-room build separate from GitHub's hosted runners:

1. **Checkout** — pulls the latest commit from the GitHub repository.
2. **Set Up Environment** — creates a fresh virtual environment and
   installs dependencies (nothing is reused from a previous build).
3. **Build** — byte-compiles the application to catch syntax errors.
4. **Lint** — runs `flake8` against the source.
5. **Unit Tests** — runs the Pytest suite and publishes JUnit-format
   results via the `junit` post-build step.
6. **Docker Build** — builds the Docker image, tagged with the Jenkins
   `BUILD_NUMBER`.

**How to configure this in Jenkins:**
1. Install the *Git*, *Pipeline*, and *JUnit* plugins.
2. Create a new **Pipeline** job → *Pipeline script from SCM* → point it
   at this repository's `Jenkinsfile`.
3. Set up a **GitHub webhook** (or poll SCM) so Jenkins triggers a build
   automatically on every push, mirroring the GitHub Actions trigger.
4. Ensure the Jenkins agent has Python 3.12 and Docker installed.

### 5.3 Why both Jenkins *and* GitHub Actions?

GitHub Actions provides fast, cloud-hosted validation on every push/PR
directly inside GitHub. Jenkins provides an independent, self-hosted
"quality gate" build — useful in real organizations where an internal
build server enforces additional compliance or infrastructure checks
before code is considered production-ready. Together they give the
project two independent confirmations that the build is healthy.

---

## 6. Git Workflow / Version Control Strategy

- `main` — always deployable; protected branch. Nothing is committed to
  it directly; every change lands via a merged branch.
- `feature/<short-description>` — new functionality
  (e.g. `feature/client-management`, `feature/progress-tracking`)
- `fix/<short-description>` — bug fixes
  (e.g. `fix/negative-weight-validation`)
- `infra/<short-description>` — tooling/infrastructure
  (e.g. `infra/docker-setup`, `infra/github-actions`, `infra/jenkins`)

Commit messages follow a conventional, descriptive style
(`feat:`, `fix:`, `infra:`, `test:`, `docs:` prefixes).

### Actual branch-by-branch history used for this project

| # | Branch | Commit message | Merged into `main` via |
|---|--------|-----------------|--------------------------|
| 1 | `feature/flask-skeleton` | `feat: initial Flask app skeleton with health check` | PR #1 |
| 2 | `feature/client-management` | `feat: implement client management endpoints` | PR #2 |
| 3 | `feature/progress-tracking` | `feat: add calorie calculation and progress tracking` | PR #3 |
| 4 | `test/pytest-suite` | `test: add pytest suite covering core logic and validation` | PR #4 |
| 5 | `infra/docker-setup` | `infra: add multi-stage, non-root Dockerfile` | PR #5 |
| 6 | `infra/github-actions` | `infra: add GitHub Actions CI/CD workflow` | PR #6 |
| 7 | `infra/jenkins` | `infra: add Jenkinsfile for Jenkins BUILD stage` | PR #7 |
| 8 | `fix/validation-edge-cases` | `fix: reject negative weight/age and out-of-range adherence` | PR #8 |
| 9 | `docs/readme` | `docs: add README with setup and pipeline documentation` | PR #9 |

This mirrors real engineering practice: each concern is isolated on its
own branch, reviewed (even solo, via a self-merged PR), and only then
integrated into `main` — which is what triggers the GitHub Actions
pipeline on every push/PR as required by the brief.

---

## 7. Docker Image Notes (Efficiency & Security)

- Based on `python:3.12-slim` (small footprint, no build toolchain).
- Dependency layer is installed **before** copying application code, so
  Docker's layer cache is reused whenever only `app.py` changes.
- Runs as a **non-root user** (`appuser`).
- `.dockerignore` excludes tests, git metadata, and virtual environments
  from the build context.
- Uses `gunicorn` as the production WSGI server rather than Flask's
  built-in development server.
- Includes a `HEALTHCHECK` so orchestrators can detect an unhealthy
  container.

---

## 8. Evaluation Checklist (Self-Verification)

- [x] Flask application runs and exposes documented endpoints.
- [x] Meaningful, logically structured Git commits (see §6).
- [x] Pytest suite covers core functionality (CRUD, validation, business
      logic, error paths).
- [x] Dockerfile is small, cached efficiently, and runs as non-root.
- [x] Jenkinsfile performs an independent clean BUILD.
- [x] GitHub Actions workflow triggers on every push/PR and runs
      Build & Lint → Docker Assembly → Pytest-in-container.
- [x] README documents setup, manual test execution, and pipeline logic.
