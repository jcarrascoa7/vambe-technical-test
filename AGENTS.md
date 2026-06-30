# AGENTS.md — Navigation Map for AI Agents

> This file is the **entry point** for any agent working in this repository.
> It is NOT a rule bible: it is a **map**. Read only what you need, when you need
> it (progressive disclosure).

---

## 1. Before You Start (mandatory)

1. Run `./init.sh` and verify all checks pass.
   - If Docker steps show `[WARN]` (not installed or no `docker-compose.yml`), that's **expected** — it means feature 0 (bootstrap) hasn't been done yet. Proceed to step 2.
   - If Docker steps show `[FAIL]`, **stop** and fix the environment before touching any code.
2. Read `progress/current.md` to understand where the last session left off.
3. Read `feature_list.json` and pick **one** task with status `pending` whose `depends_on` are all `done`. Do NOT work on more than one task at a time.

## 2. Repository Map

| File / Folder | What It Contains | When to Read It |
|---|---|---|
| `feature_list.json` | Task list with status (pending / in_progress / done) | Always, at session start |
| `progress/current.md` | Current session state | Always, at session start |
| `progress/history.md` | Append-only log of past sessions | When you need historical context |
| `docs/domain.md` | Problem definition: context, dimensions, categories, metrics, visualizations | Before implementing any categorization, metric, or dashboard feature |
| `docs/architecture.md` | What "doing a good job" means in this project | Before implementing |
| `docs/tech-stack.md` | Technology choices with justification and project structure | Before implementing or modifying infra |
| `docs/conventions.md` | Style rules, naming, structure, git, clean code | Before writing code |
| `docs/verification.md` | How to verify your work is correct | Before marking a task as `done` |
| `CHECKPOINTS.md` | Objective criteria for "correct final state" | For self-evaluation |
| `.claude/agents/` | Sub-agent definitions for Claude Code (leader, implementer, reviewer, explorer, pr-agent) | When orchestrating work |
| `.opencode/agents/` | Sub-agent definitions for opencode (same agents, opencode format) | When orchestrating work in opencode |
| `backend/` | FastAPI application, ETL, categorizer, API routes | For implementation |
| `backend/etl/` | CSV cleaning (pandas), signal extraction (regex), DB loading | When working on data pipeline |
| `backend/categorizer/` | LLM prompts, Gemma 4 client, batch processing, validation | When working on categorization |
| `backend/api/routes/` | API endpoints: clients (filters, search), metrics (aggregations) | When working on API layer |
| `backend/tests/` | pytest tests for ETL, categorizer, API | For verification |
| `frontend/` | React + Vite + Chart.js + Tailwind dashboard | When working on UI |
| `frontend/src/components/` | Dashboard, Filters, KPICards, Charts, ClientTable | When building UI components |
| `frontend/src/hooks/` | Custom React hooks (useFilters) | When working on filter logic |
| `frontend/src/api/` | Axios/fetch wrapper for backend communication | When modifying API calls |
| `data/` | Source CSV (vambe_clients_10k.csv) | When working on ETL or testing |
| `docker-compose.yml` | Container orchestration: app + PostgreSQL | When modifying infra |
| `Dockerfile` | App container definition | When modifying build process |

## 3. Hard Rules (non-negotiable)

- **One feature at a time.** Do not mix changes from multiple tasks in the same session.
- **Never declare a task `done` without green tests.** Run `docker compose up --build` and ensure the test suite passes at 100% (or shows `[WARN] No tests found` for features that don't produce tests).
- **Document as you go** in `progress/current.md` while working, not after the fact.
- **Leave the repository clean** before ending a session (see §5).
- **If you don't know something, check `docs/`** before inventing a solution.

## 4. How to Pick a Task

```
1. Open feature_list.json
2. Filter by status == "pending"
3. Pick the one with the lowest "id"
4. Change its status to "in_progress" and save
5. Note in progress/current.md: feature, start time, brief plan
```

## 5. Session Lifecycle (shutdown)

Before ending:

1. Run `./init.sh` — all steps green (or `[WARN]` for Docker steps if doing feature 0).
2. If the task is complete: mark `status: "done"` in `feature_list.json`.
3. Move the summary from `progress/current.md` to the end of `progress/history.md`.
4. Empty `progress/current.md` leaving only the template.
5. Do not leave temp files, debug `print()` statements, or TODOs without context.

## 6. If You Get Stuck

- Re-read the relevant section in `docs/`.
- If the tool doesn't behave as expected, **do not invent a workaround**:
  document the blocker in `progress/current.md` and end the session.

## 7. Environment Variables

> **NEVER read `.env`.** It contains secrets. Read `.env.example` for variable names and this section for documentation.

### Required Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string (used by SQLAlchemy) | `postgresql://postgres:postgres@db:5432/vambe` |
| `POSTGRES_USER` | PostgreSQL username (must match `DATABASE_URL`) | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password (must match `DATABASE_URL`) | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name (must match `DATABASE_URL`) | `vambe` |
| `GEMMA_API_KEY` | API key for Gemma 4 (Google AI Studio) | `your_api_key_here` |
| `GEMMA_API_URL` | Gemma 4 API endpoint | `https://generativelanguage.googleapis.com/v1beta/models/gemma-4:generateContent` |
| `MAX_RECORDS_TO_CATEGORIZE` | Max records the categorizer processes (1000 for demo, 10000 for full) | `1000` |

### Notes

- `GEMMA_API_KEY` is **required** for the categorizer to work. Without it, the app starts but categorization fails silently.
- `DATABASE_URL` uses the Docker service name `db` as hostname, not `localhost`. This works inside Docker Compose networking.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` must match the credentials in `DATABASE_URL`.
