# TracePilot 🚀

### Evidence-Driven Release Regression Investigation Platform

TracePilot is a full-stack software engineering project designed to compare software releases, detect statistically significant changes in error rates, organize investigation evidence, and generate structured findings with explicit limitations.

It helps developers investigate whether a candidate release shows signs of regression compared with a baseline release, without automatically assuming that a detected regression identifies its root cause.

## ✨ Features

- **Release Management** — Create and retrieve baseline and candidate releases.
- **Regression Detection** — Evaluate error-rate changes using statistical tests and configurable thresholds.
- **Release Comparison** — Compare error rates and average response durations between releases.
- **Investigation Management** — Create investigations, retrieve details, and manage investigation status.
- **Evidence Management** — Store evidence and associate it with investigations.
- **Structured Findings** — Summarize investigation conclusions and supporting evidence.
- **Evidence Quality Assessment** — Represent evidence quality and identify limitations.
- **REST API** — Expose backend functionality through FastAPI endpoints.
- **Interactive Dashboard** — Access release comparisons and investigation workflows through a React frontend.
- **Automated Testing** — Validate backend behavior using pytest and FastAPI's test client.

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Data Validation | Pydantic |
| Database Layer | SQLAlchemy |
| Database | SQLite for local development |
| Frontend | React, TypeScript |
| Frontend Tooling | Vite, npm |
| Testing | pytest, FastAPI TestClient |
| Code Quality | Ruff |
| Version Control | Git, GitHub |

## 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │   React Dashboard    │
                    │   TypeScript + Vite  │
                    └──────────┬───────────┘
                               │ HTTP / REST
                    ┌──────────▼───────────┐
                    │      FastAPI         │
                    │     REST API         │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼──────┐ ┌───────▼────────┐ ┌─────▼──────────┐
     │   Releases &  │ │ Investigations │ │    Evidence    │
     │    Metrics    │ │  & Findings    │ │   Management   │
     └────────┬──────┘ └───────┬────────┘ └─────┬──────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │ SQLAlchemy Database  │
                    │  SQLite (local)      │
                    └──────────────────────┘
```

## 🔍 How It Works

1. Register baseline and candidate software releases.
2. Record release-associated events.
3. Compare release metrics, including error rates and response duration.
4. Evaluate error-rate changes against statistical and practical thresholds.
5. Create an investigation to examine a suspected regression.
6. Attach supporting evidence to the investigation.
7. Retrieve structured findings, evidence quality, and known limitations.
8. Use the findings to guide further debugging and validation.

## 📊 Regression Analysis

TracePilot evaluates changes in error rates using statistical methods, including a two-proportion z-test and Wilson confidence intervals.

The detection workflow considers factors such as:

- Number of recorded events per release.
- Difference in error rates.
- Minimum practical change threshold.
- Statistical significance level.
- Whether the available sample size is sufficient for an assessment.

The system distinguishes between insufficient evidence, detected regression signals, no detected regression signal, and inconclusive results.

**Important:** Statistical significance is not proof of causation. A detected regression signal does not establish which code change, service, or dependency caused the observed behavior.

## 🚀 Getting Started

### Prerequisites

Install the following:

- Python 3.11 or a compatible version supported by the project dependencies.
- Node.js and npm.
- Git.

### 1. Clone the repository

Replace the placeholder with your actual GitHub repository URL.

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd TracePilot
```

### 2. Set up the backend

From the project root, create and activate a virtual environment.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start the backend:

```powershell
uvicorn app.main:app --reload
```

Backend API:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

Alternative API documentation:

`http://127.0.0.1:8000/redoc`

### 3. Set up the frontend

Open a second terminal:

```powershell
cd D:\TracePilot\frontend
npm ci
npm run dev
```

Open the local frontend URL printed by Vite in your terminal.

### 4. Run backend tests

From the project root:

```powershell
cd D:\TracePilot\backend
python -m pytest -q
```

### 5. Run code-quality checks

```powershell
cd D:\TracePilot\backend
ruff check app tests
```

### 6. Build the frontend

```powershell
cd D:\TracePilot\frontend
npm run build
```

## 📡 API Overview

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | Check backend health |
| `POST /api/v1/releases` | Create a release |
| `GET /api/v1/releases` | Retrieve releases |
| `POST /api/v1/events` | Record events |
| `GET /api/v1/events` | Retrieve events |
| `GET /api/v1/metrics/release` | Retrieve release metrics |
| `GET /api/v1/metrics/compare` | Compare baseline and candidate metrics |
| `POST /api/v1/evidence` | Store investigation evidence |
| `GET /api/v1/evidence` | Retrieve evidence |
| `POST /api/v1/investigations` | Create an investigation |
| `GET /api/v1/investigations` | Retrieve investigations |
| `GET /api/v1/investigations/{investigation_id}` | Retrieve investigation details |
| `PATCH /api/v1/investigations/{investigation_id}/status` | Update investigation status |
| `GET /api/v1/investigations/{investigation_id}/summary` | Retrieve an investigation summary |
| `GET /api/v1/investigations/{investigation_id}/findings` | Retrieve structured findings |

For request and response schemas, run the application and visit `/docs`.

## 🧪 Testing and Quality

The project includes automated tests for core regression logic, release comparisons, API behavior, investigation management, evidence handling, and investigation workflows.

The development verification process includes:

- Backend tests with pytest.
- Static linting with Ruff.
- Frontend production builds with Vite.

Run the commands above to verify the current state of your local checkout.

## ⚠️ Limitations

- A statistical regression signal does not prove causation or establish root cause.
- Small sample sizes may limit the reliability of comparisons.
- Findings depend on the quality and completeness of stored evidence.
- Stored statistical assessments are not necessarily independently recalculated or verified by the findings engine.
- Synthetic or demonstration events should not be treated as production telemetry.
- Authentication, production deployment, and operational security must be assessed separately before using the application in a real production environment.

## 🗺️ Future Improvements

Potential extensions include:

- Read-only tools for AI agents to inspect releases, metrics, and evidence.
- LLM-assisted investigation summaries with traceable evidence references.
- Integration with production telemetry and monitoring platforms.
- PostgreSQL support for deployment environments.
- Authentication, role-based access control, and audit logging.
- Automated CI checks and deployment workflows.

## 👨‍💻 Author

**Yash Kalbhile**

GitHub: https://github.com/yash45615

LinkedIn:  https://www.linkedin.com/in/yash-kalbhile-697727231/

## 📄 License

Choose and add a license before publishing if you want to specify how others may use, modify, and distribute this project.
