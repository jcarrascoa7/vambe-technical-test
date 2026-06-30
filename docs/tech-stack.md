# Tech Stack

> Technology choices with justification. Every tool here solves a specific problem.

---

## Stack Overview

| Component | Technology | Justification |
|---|---|---|
| **Backend** | FastAPI (Python) | Python is already needed for pandas and the Gemma 4 API. One language across the entire backend. FastAPI generates automatic OpenAPI documentation (bonus for evaluation). Native async for concurrent LLM calls |
| **ETL** | Python module + pandas inside the backend | Not a separate microservice: ETL runs once at startup. As a backend module, it's imported and executed without network communication overhead |
| **Categorization** | Python module + HTTP client (httpx) to Gemma 4 | Same language, independent module with single responsibility. Batches of 50-100 records with checkpoints in the DB |
| **Database** | PostgreSQL (Docker) | Supports complex queries for combined filters and metric aggregations. SQLAlchemy as ORM. Evaluator sees relational DB usage |
| **Frontend** | React + Vite + Chart.js + Tailwind | Modern, responsive frontend with interactive charts. Vite for fast builds. Tailwind for clean UI without extensive custom CSS |
| **Containerization** | Docker Compose | 2 containers: app (FastAPI + React build served as static) + PostgreSQL. Single `docker compose up` starts everything |
| **Deploy** | Railway (free tier) | Supports Docker natively. 500 hours/month and 1GB RAM free, sufficient for this case |

---

## Project Structure

```
vambe-dashboard/
├── docker-compose.yml
├── Dockerfile
├── README.md
├── .env.example
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── backend/
│   ├── main.py                 # FastAPI app, startup logic
│   ├── config.py               # Settings, DB connection string
│   ├── database.py             # SQLAlchemy engine + session
│   ├── models.py               # SQLAlchemy models (Client, MetricCache)
│   ├── etl/
│   │   ├── cleaner.py          # CSV cleaning (pandas)
│   │   └── loader.py           # Load to PostgreSQL
│   ├── categorizer/
│   │   ├── prompts.py          # Structured prompts + few-shot
│   │   ├── gemma_client.py     # Async httpx client for Gemma 4
│   │   ├── processor.py        # Batch orchestration
│   │   └── validator.py        # Category validation against lists
│   ├── api/
│   │   ├── routes/
│   │   │   ├── clients.py      # GET /clients (filters, search, pagination)
│   │   │   └── metrics.py      # GET /metrics/* (aggregations)
│   │   └── schemas.py          # Pydantic response models
│   ├── static/                 # React build output
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Filters.jsx
│   │   │   ├── KPICards.jsx
│   │   │   ├── Charts/
│   │   │   │   ├── CloseRateBySector.jsx
│   │   │   │   ├── VendorHeatmap.jsx
│   │   │   │   ├── PainDistribution.jsx
│   │   │   │   ├── CloseRateBySource.jsx
│   │   │   │   ├── ConcretividadChart.jsx
│   │   │   │   ├── TimelineChart.jsx
│   │   │   │   └── IntegrationsTreemap.jsx
│   │   │   └── ClientTable.jsx
│   │   ├── hooks/
│   │   │   └── useFilters.js
│   │   └── api/
│   │       └── client.js       # Axios/fetch wrapper
│   ├── package.json
│   └── vite.config.js
└── data/
    └── vambe_clients_10k.csv
```

---

## Deployment

### Local (development)
```bash
git clone <repo>
docker compose up --build
# App at http://localhost:8000
# First startup runs ETL + categorization automatically
```

### Production (Railway — free)
- Push repo to GitHub
- Connect Railway to repo
- Railway detects `Dockerfile` and `docker-compose.yml`
- Exposes port 8000 publicly
- Functional link for the evaluator

---

## CI/CD

### GitHub Actions

Automated pipeline that runs on every push and pull request. Ensures code quality before merging.

| Workflow | Trigger | What it does |
|---|---|---|
| **CI** (`ci.yml`) | `push`, `pull_request` | Lint (ruff + black), build Docker, run pytest, build frontend |
| **Deploy** (`deploy.yml`) | `push` to `main` | Deploy to Railway (placeholder until Railway is configured) |

### CI Pipeline Steps

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint Python (ruff)
        run: pip install ruff && ruff check backend/
      - name: Format check (black)
        run: pip install black && black --check backend/
      - name: Build containers
        run: docker compose build
      - name: Run tests
        run: docker compose up -d && docker compose exec -T app pytest backend/tests/ -v
      - name: Frontend build
        run: docker compose exec -T app sh -c "cd frontend && npm run build"
```

### Design Decisions

- **Linting before build**: Fail fast on style issues before spending time on Docker build.
- **Tests inside Docker**: Matches production environment. Avoids "works on my machine" issues.
- **Separate CI and Deploy**: CI runs everywhere. Deploy only on main branch pushes.

---

## Design Decisions

### Monorepo

Frontend and backend share one repo. Frontend builds to static files served by FastAPI.

| Alternative | Reason for discard |
|---|---|
| **Separate repos (frontend / backend)** | Over-engineering for a project of this size. Docker Compose expects everything in one directory. Railway deploys from a single repo. Frontend build is served statically from the backend, it's not an independent service. |

### 1,000 Record Limit

The categorizer processes 1,000 records (10% of dataset) instead of the full 10,000.

- **API cost**: Gemma 4 is free, but has rate limits. 10,000 calls with long prompts take hours.
- **Processing time**: ~2 seconds per call. 1,000 records ≈ 33 min. 10,000 ≈ 5.5 hours.
- **Demonstrability**: 1,000 records are sufficient to prove the concept works.
- **Scalability**: Architecture supports 10,000+ by changing `MAX_RECORDS_TO_CATEGORIZE`.

### Idempotent Startup

Each record has `categorized: boolean` (default `false`). On startup:
1. If `clients` table is empty → run ETL
2. If uncategorized records exist → run categorizer in background
3. Categorizer only processes `WHERE categorized = false`
4. After each batch: `UPDATE SET categorized = true`
5. If app restarts mid-process, it resumes where it left off

### Partial Metrics During Categorization

While categorization runs in background, the dashboard is functional with already-processed data:
- Frontend shows a progress bar + "X% categorized" badge
- "Refresh metrics" button updates data without restarting
- Metrics are calculated only on categorized records
- Filters work normally (filter by `categorized = true`)
