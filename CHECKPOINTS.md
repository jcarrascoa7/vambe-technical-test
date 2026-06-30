# CHECKPOINTS — Final State Evaluation

> In multi-agent systems you evaluate the destination, not the path.
> These are the objective checkpoints a judge (human or AI) can use
> to decide if the project is healthy.

## C1 — The Harness Is Complete

- [ ] Base files exist: `AGENTS.md`, `init.sh`, `feature_list.json`, `progress/current.md`, `.env.example`.
- [ ] Docs exist: `docs/architecture.md`, `docs/conventions.md`, `docs/verification.md`, `docs/domain.md`, `docs/tech-stack.md`.
- [ ] Agent definitions exist: `.claude/agents/leader.md`, `.claude/agents/implementer.md`, `.claude/agents/reviewer.md`, `.claude/agents/explorer.md`, `.claude/agents/pr-agent.md`.
- [ ] `./init.sh` exits with code 0.

## C2 — The State Is Coherent

- [ ] At most one feature in `in_progress` in `feature_list.json`.
- [ ] Every feature marked `done` has associated tests that pass (if the feature produces tests).
- [ ] `progress/current.md` is empty or describes the active session (no garbage from past sessions).

## C3 — The Code Respects the Architecture

- [ ] `backend/` contains only the modules defined in `docs/tech-stack.md`: `etl/`, `categorizer/`, `api/`.
- [ ] `frontend/` contains only the React app: `src/components/`, `src/hooks/`, `src/api/`.
- [ ] `requirements.txt` includes only the expected dependencies (fastapi, uvicorn, sqlalchemy, pandas, httpx, pytest).
- [ ] No stray debug `print()` statements, no TODOs without context.
- [ ] `docker-compose.yml` defines exactly two services: `app` and `db`.

## C4 — The Verification Is Real

- [ ] `backend/tests/` has at least one test per module (`test_etl.py`, `test_extractor.py`, `test_categorizer.py`, `test_gemma_client.py`, `test_processor.py`, `test_schemas.py`, `test_api_clients.py`, `test_api_metrics.py`).
- [ ] Tests use SQLite in-memory for DB fixtures, not the production PostgreSQL.
- [ ] `docker compose exec app pytest backend/tests/ -v` shows all green (or `[WARN] No tests found` for features that don't produce tests).
- [ ] `docker compose up --build` starts without errors and app is reachable at `http://localhost:8000`.

## C5 — The Session Was Closed Properly

- [ ] No suspicious untracked files (`*.tmp`, `__pycache__` outside `.gitignore`).
- [ ] `progress/history.md` has an entry for the latest session.
- [ ] The last feature worked on is reflected in its correct status in `feature_list.json`.
- [ ] No debug `print()` statements left in committed code.

---

**How to use this file:** a reviewer agent (`.claude/agents/reviewer.md`) walks through each checkbox, marks `[x]` or `[ ]`, and rejects the session close if any boxes in C1–C5 are empty.
