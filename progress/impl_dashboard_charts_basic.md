# Implementation Summary — Feature 11: Dashboard Charts (Basic)

## Files Modified

- `frontend/package.json` — added chart.js, react-chartjs-2, chartjs-plugin-annotation
- `frontend/src/App.jsx` — imported and rendered 5 chart components in grid layout
- `frontend/src/components/Charts/CloseRateBySector.jsx` — new: horizontal bar chart, sorted descending
- `frontend/src/components/Charts/SectorDistribution.jsx` — new: donut chart with 17-color palette
- `frontend/src/components/Charts/PainDistribution.jsx` — new: 100% stacked bar chart
- `frontend/src/components/Charts/CloseRateBySource.jsx` — new: bar chart with global avg reference line (annotation plugin)
- `frontend/src/components/Charts/CloseRateByConcreteness.jsx` — new: bar chart with color-coded gap highlight
- `backend/api/routes/metrics.py` — added filter params (sector, size, volume, source, channel, vendor, closed, date_from, date_to) to: close-rate-by-source, pain-distribution-by-sector, sector-distribution, close-rate-by-concreteness
- `backend/tests/test_api_metrics.py` — added filter acceptance tests for 4 endpoints

## Key Decisions

- Used chartjs-plugin-annotation for the global average reference line on CloseRateBySource (standard Chart.js approach)
- PainDistribution computes percentages client-side (count/sector_total * 100) for 100% stacked bars
- CloseRateByConcreteness colors highest green, lowest red, others blue to highlight the gap
- All charts receive `apiParams` from useFilters hook — filter changes trigger re-fetch via useEffect dependency
- All 5 chart-related API endpoints now accept the same filter params as close-rate-by-sector

## Acceptance Criteria Coverage

1. ✅ Bar chart shows close rate by sector (sorted descending) — CloseRateBySector.jsx
2. ✅ Donut chart shows sector distribution — SectorDistribution.jsx
3. ✅ Stacked bar chart shows pain distribution by sector (100% stacked) — PainDistribution.jsx
4. ✅ Bar chart shows close rate by acquisition source with global average reference line — CloseRateBySource.jsx
5. ✅ Bar chart shows close rate by language concreteness with highlighted gap — CloseRateByConcreteness.jsx
6. ✅ Charts respond to filter changes — all components use apiParams, backend endpoints accept filter params
