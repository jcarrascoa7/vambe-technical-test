# Verification — How to Prove Your Work Works

> Golden rule: **the agent doesn't say "it works", it proves it.**
> Every feature ends with executable evidence, not with claims.

---

## How to Verify Your Work Is Correct

### Before declaring any task "done":

1. **Run the full stack**: `docker compose up --build`
   - App starts without errors
   - ETL runs (if first time) or is skipped
   - Categorization runs in background
   - Dashboard is accessible at `http://localhost:8000`

2. **Run the test suite**:
   ```bash
   docker compose exec app pytest backend/tests/ -v
   ```
   All tests must pass. If no tests exist yet (e.g. scaffolding, CI features), `[WARN] No tests found` is acceptable.

3. **Manual smoke test** (for API tasks):
   - `GET /clients` returns data
   - `GET /clients?sector=Salud` filters correctly
   - `GET /metrics/close-rate-by-sector` returns aggregated data
   - `GET /metrics/status` shows categorization progress

### Module-specific verification

| Module | Command | Expected |
|---|---|---|
| ETL | `pytest backend/tests/test_etl.py -v` | CSV loads, dates parse, nulls handled |
| Extractor | `pytest backend/tests/test_extractor.py -v` | Regex extracts signals correctly |
| Categorizer | `pytest backend/tests/test_categorizer.py -v` | Validation catches bad categories |
| API clients | `pytest backend/tests/test_api_clients.py -v` | Filters and search work |
| API metrics | `pytest backend/tests/test_api_metrics.py -v` | Aggregations are correct |

### Common failure modes

- **Tests pass locally but fail in Docker**: DB is different (SQLite vs PostgreSQL).
- **Categorizer returns wrong categories**: Check prompt formatting, not the validation logic.
- **Filters return no results**: Check SQLAlchemy query construction with `.filter()` chaining.
- **Frontend charts empty**: Verify API returns data, check CORS, check network tab.

---

## Anti-patterns (do not do)

- ❌ "I added the command, it should work." → missing executable test.
- ❌ Test that only checks the function doesn't raise an exception. → must verify the concrete result.
- ❌ `mock` of the filesystem. → use real `tempfile.TemporaryDirectory()`.
- ❌ Marking the feature as `done` without running `./init.sh`.

## Final verification before closing

```bash
./init.sh           # must end with [OK] Environment ready
```

If `./init.sh` is red, do **not** mark anything as `done`. Note the blocker
in `progress/current.md` and set `status: "blocked"` in `feature_list.json`.
