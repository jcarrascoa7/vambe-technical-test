# Feature 7 — api_metrics_endpoints

## Files Modified

- `backend/api/routes/metrics.py` (new) — 12 metric endpoints + status endpoint
- `backend/main.py` — registered metrics router
- `backend/tests/test_api_metrics.py` (new) — 26 tests covering all endpoints + zero records edge case

## Key Decisions

- **Temporal evolution uses Python-side grouping** instead of `to_char()` (PostgreSQL-only). Fetches raw dates and groups by `YYYY-MM` in Python for SQLite test compatibility. Works identically on PostgreSQL.
- **Integrations are split by comma** in `integrations-distribution` — the column stores comma-separated values like "CRM, ERP".
- **Inquiry volume is mapped to numeric midpoints** (Low=250, Medium=1250, High=3500, Very High=7500) for `avg-volume-by-sector` and `top-sectors-by-volume-rate`.
- **"Not specified" exclusion** applied to every metric that depends on a categorization dimension, per domain.md Data Exclusion Rule.
- **Status endpoint** on `/metrics/status` (separate from `/clients/status` which already existed).
- **Reused `MetricResponse`** schema from feature 6 — no changes needed to schemas.py.

## Test Coverage

- 14 test classes: one per metric endpoint + zero records edge case class (12 tests)
- Tests verify: correct aggregation, "Not specified" exclusion, zero records returns empty/zero
- All 120 tests in the full suite pass (94 existing + 26 new)
