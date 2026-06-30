# Review — feature 11 (dashboard_charts_basic)

**Verdict:** APPROVED

## Checkpoints

- C1: [x] All harness base files, docs, and agent definitions exist. `./init.sh` exits with code 0.
- C2: [x] Only feature 11 is `in_progress`. All `done` features have passing tests. `progress/current.md` describes active session.
- C3: [x] Backend structure matches `docs/tech-stack.md`. Frontend has `src/components/Charts/`, `src/hooks/`, `src/api/`. `package.json` adds only expected deps: `chart.js`, `react-chartjs-2`, `chartjs-plugin-annotation`. No stray files, no debug prints. `docker-compose.yml` defines exactly two services: `app` and `db`.
- C4: [x] 124 tests pass (all green). Tests use SQLite in-memory fixtures. New tests added in `test_api_metrics.py` for filter params on `close-rate-by-source`, `pain-distribution-by-sector`, `close-rate-by-concreteness`, `sector-distribution`. `./init.sh` green.
- C5: [x] No suspicious untracked files. Feature 11 is `in_progress` (correct for review stage).

## Acceptance Criteria

- [x] Bar chart: close rate by sector (sorted descending) — `CloseRateBySector.jsx`
- [x] Donut chart: sector distribution — `SectorDistribution.jsx`
- [x] Stacked bar chart: pain distribution by sector (100% stacked) — `PainDistribution.jsx`
- [x] Bar chart: close rate by source with global average reference line (annotation plugin) — `CloseRateBySource.jsx`
- [x] Bar chart: close rate by concreteness with highlighted gap — `CloseRateByConcreteness.jsx`
- [x] Charts respond to filter changes (all components accept `apiParams` prop, re-fetch on change)

## Changes Reviewed

| File | Change | Status |
|---|---|---|
| `frontend/src/components/Charts/CloseRateBySector.jsx` | New: bar chart, sorted descending, Chart.js | OK |
| `frontend/src/components/Charts/SectorDistribution.jsx` | New: doughnut chart with color palette | OK |
| `frontend/src/components/Charts/PainDistribution.jsx` | New: 100% stacked bar, pain colors map | OK |
| `frontend/src/components/Charts/CloseRateBySource.jsx` | New: bar + annotation plugin reference line | OK |
| `frontend/src/components/Charts/CloseRateByConcreteness.jsx` | New: bar + gap highlight text | OK |
| `frontend/src/App.jsx` | Import and render 5 charts in grid, pass `apiParams` | OK |
| `frontend/package.json` | Added `chart.js`, `react-chartjs-2`, `chartjs-plugin-annotation` | OK |
| `backend/api/routes/metrics.py` | Added filter params to 4 endpoints (source, pain, concreteness, sector-dist) for frontend filter support | OK |
| `backend/tests/test_api_metrics.py` | Added `test_accepts_filter_params` for 4 newly-filtered endpoints | OK |

## Architecture Compliance

- **Frontend**: Components are presentational (receive `apiParams`, fetch data, render). Logic in `useFilters` hook and `api/client.js`. Chart.js used throughout. Tailwind for styling.
- **Backend**: Routes validate input and call DB — no business logic extracted into separate service for this simple aggregation pattern (consistent with existing codebase). Filter logic already extracted into `_apply_filters()`.
- **Dependencies**: Only Chart.js ecosystem added. No new backend deps.

## Notes

- `ChartPlaceholder` (6 lines) is duplicated across 5 chart files. Minor DRY concern but acceptable — trivial JSX, not logic.
- Filter params are repeated across endpoint signatures in `metrics.py` — could use FastAPI `Depends()` but consistent with existing pattern (pre-existing from features 7/9).
