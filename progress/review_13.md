# Review — feature 13

**Verdict:** APPROVED

## Checkpoints
- C1: [x]
- C2: [x]
- C3: [x]
- C4: [x]
- C5: [x]

## Acceptance Criteria
- `.github/workflows/ci.yml` triggered on push and pull_request: ✅ (lines 3-5)
- Python linting (ruff) and formatting (black --check): ✅ (lines 18-22)
- Frontend linting (eslint + prettier): ✅ (lines 29-35, `.eslintrc.cjs` + scripts in package.json)
- Docker build with `docker compose build`: ✅ (line 41)
- pytest inside container: ✅ (line 59, `docker compose exec -T app pytest backend/tests/ -v`)
- Frontend build inside container: ✅ (line 62, `npm ci && npm run build`)
- Fail fast: ✅ (single job, steps are sequential — GitHub Actions fails the job on first failing step)
- `.github/workflows/deploy.yml` Railway placeholder on push to main: ✅ (lines 1-16)

## Notes
- `ruff` and `black` added to `backend/requirements.txt` — minor (they end up in prod image), acceptable for test project
- `pyproject.toml` configures ruff with sensible defaults (line-length 88, ignores E712/E501)
- `frontend/.eslintrc.cjs` and `prettier` added as devDependencies with `lint` and `format:check` scripts
- `./init.sh` passes all green
