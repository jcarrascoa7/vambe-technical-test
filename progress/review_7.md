# Review — feature 7 (api_metrics_endpoints)

**Verdict:** APPROVED

## Checkpoints
- C1: [x] — All harness files and docs exist, `./init.sh` exits 0.
- C2: [x] — Feature 7 is the only `in_progress`. Progress/current.md describes active session.
- C3: [x] — `backend/api/routes/metrics.py` fits `api/routes/` per tech-stack. No stray modules. No debug `print()`. `docker-compose.yml` defines exactly `app` + `db`.
- C4: [x] — `backend/tests/test_api_metrics.py` exists (26 tests), uses SQLite in-memory, all pass. Matches `test_api_metrics.py` in C4 checklist.
- C5: [x] — No suspicious untracked files. Feature 7 is `in_progress` in `feature_list.json`.

## Detailed Review

### Architecture Compliance
- Routes do SQLAlchemy queries + result formatting — no business logic extracted to separate module is fine per `docs/architecture.md` anti-patterns ("no need for service layers, repositories, or factories in a project this size").
- Metric aggregations are SQL-level (`func.count`, `func.sum`, `case`) with Python post-processing only where needed (volume mapping, temporal grouping, integrations splitting). Clean separation.
- `temporal_evolution` uses Python-side date grouping with `ponytail:` comment explaining DB-agnostic rationale — acceptable.
- Router registered in `main.py` with minimal diff (2 lines: import + `include_router`).

### Conventions Compliance
- `snake_case` functions, `PascalCase` classes, Google docstrings on all endpoints.
- Type hints on all function signatures.
- Imports: stdlib → third-party → local (correct order).
- No comments except `ponytail:` markers (allowed).
- All functions under 20 lines of logic.
- `_categorized_only()` helper reduces duplication across 10 close-rate endpoints.

### Domain Compliance
- All 12 metric endpoints match acceptance criteria 1:1.
- `NOT_SPECIFIED` filter applied on the correct dimension per endpoint (data exclusion rule from `docs/domain.md`).
- Metrics query only `categorized == True` records (partial data support).
- `_VOLUME_MAP` maps categories to numeric midpoints for averaging — matches domain definition (Low <500, Medium 500-2k, High 2k-5k, Very High >5k).
- Integrations splitting on comma handles multi-value field correctly.

### Test Quality
- 26 tests: 14 happy-path + 12 zero-records edge cases (one per endpoint + status).
- Tests verify concrete values (close rates, counts, percentages), not just "doesn't raise".
- `Not specified` exclusion explicitly tested (`test_excludes_not_specified`).
- Status endpoint tested for both partial and complete states.
- DB fixtures use SQLAlchemy `create_all/drop_all` per test — isolated and repeatable.

### Schema
- `MetricResponse` uses Pydantic v2 `Generic[T]` — matches feature 6 acceptance criterion.
- `StatusResponse` includes `Field(ge=0, le=100)` validation on `progress`.

## Minor Notes (non-blocking)
1. `GET /clients/status` and `GET /metrics/status` have identical logic — potential DRY opportunity but not a violation (already existed from feature 6).
2. `top_sectors_by_volume_rate` does two separate queries — could be one with a CTE, but the current approach is clear and correct for 1,000 records.
