# Feature 13: CI/CD Pipeline — Implementation Summary

## Files Modified

| File | Change |
|---|---|
| `.github/workflows/ci.yml` | New: CI workflow (lint, Docker build, pytest, frontend build) |
| `.github/workflows/deploy.yml` | New: Deploy workflow placeholder for Railway |
| `Dockerfile` | Added Node.js binary + npm to final stage for CI frontend builds |
| `frontend/package.json` | Added eslint, prettier, eslint-plugin-react devDeps; added lint/format:check scripts |
| `frontend/.eslintrc.cjs` | New: ESLint config (react, recommended rules) |
| `backend/requirements.txt` | Added ruff and black |
| `pyproject.toml` | New: ruff config (ignore E712 for SQLAlchemy, E501 for long strings) |
| `backend/tests/test_etl.py` | Fixed ruff E712 (noqa comment for numpy bool comparison) |
| `backend/tests/test_processor.py` | Fixed ruff F841 (unused variable) |
| `backend/api/schemas.py` | Fixed ruff F401 (removed unused `Any` import) |
| `backend/tests/test_api_clients.py` | Fixed ruff F401 (removed unused `event` import) |
| `backend/tests/test_categorizer.py` | Fixed ruff F401 (removed unused `pytest` import) |
| `backend/categorizer/prompts.py` | Black formatting |
| `backend/categorizer/processor.py` | Black formatting |
| `backend/api/routes/metrics.py` | Black formatting |
| `backend/tests/test_api_metrics.py` | Black formatting |
| `backend/tests/test_gemma_client.py` | Black formatting |
| `backend/test_categorization.py` | Black formatting |
| 12 frontend source files | Prettier formatting |

## Key Decisions

- **Node.js in Dockerfile**: Copied from `frontend-build` stage so CI can run `npm ci && npm run build` inside the container. Minimal overhead (~30MB).
- **Ruff + Black installed on runner**: Linting runs on the GitHub Actions runner (fast, no Docker needed), while tests run inside Docker (matches production).
- **ESLint + Prettier for frontend**: Added as devDeps with `lint` and `format:check` scripts. Runs on the runner before Docker build.
- **E712 ignored in ruff**: SQLAlchemy `Column == True` is idiomatic; ruff's suggestion to use `Column` alone doesn't work for SQLAlchemy filter expressions.
- **E501 ignored in ruff**: Black handles code line length; long strings and comments are acceptable.
- **Deploy workflow**: Placeholder with echo. Real Railway integration needs CLI or webhook setup.
- **Fail-fast**: Each step runs in sequence; any failure stops the workflow (GitHub Actions default behavior).

## Notes for Reviewer

- The `docker compose exec -T app sh -c "cd frontend && npm ci && npm run build"` step installs node_modules inside the container at runtime. This is needed because the volume mount (`./frontend:/app/frontend`) shadows the Dockerfile's built frontend directory.
- The `.env.example` is copied to `.env` before `docker compose up` so the compose file's `env_file` directive works. The GEMMA_API_KEY placeholder doesn't affect tests (they mock the LLM).
- Tests: 124/124 passing inside Docker.
