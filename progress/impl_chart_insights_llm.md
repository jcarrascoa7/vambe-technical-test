# Implementation Summary — Feature 14: Chart Insights with LLM (Spanish)

## Files Modified

### Backend
- **`backend/api/insights.py`** (new) — `GET /insights/{chart_type}` endpoint that calls the LLM with domain-context prompts and returns Spanish explanatory text. Handles JSON and plain text responses, with fallback message on failure. Response includes a predefined short justification (<=25 words) and an LLM-generated decision paragraph.
- **`backend/main.py`** — Registered `insights_router`.
- **`backend/tests/test_insights.py`** (new) — 9 tests covering: successful LLM response, plain text response, all chart types, empty LLM fallback, malformed JSON fallback, empty text field fallback, unknown chart type, response structure consistency.

### Frontend
- **`frontend/src/api/client.js`** — Added `fetchInsight(chartType)` function.
- **`frontend/src/components/ChartInsight.jsx`** (new) — Reusable component with skeleton animation (3-bar pulse) while loading and text display on success. Uses `animate-pulse` Tailwind utility.
- **`frontend/src/App.jsx`** — Changed title to "Categorización Automática y Visualización de Métricas de Clientes". Wrapped each chart with `ChartWithInsight` that renders `ChartInsight` below the chart. Localized `CategorizationProgress` to Spanish.
- **`frontend/src/components/KPICards.jsx`** — Localized labels: "Tasa de Cierre", "Sector Principal", "Vendedor Principal".
- **`frontend/src/components/Filters.jsx`** — Localized labels: "Filtros", "Limpiar todo", "Vendedor", "Fuente", "Canal", "Cerrado", "Desde", "Hasta", "Todos", "Sí", "No".
- **`frontend/src/components/ClientTable.jsx`** — Expanded to show ALL categorized dimensions (sector, size, inquiry_volume, channel, source, integrations, tone, usage_type, pain, concreteness) plus transcription column. Localized headers, buttons, and pagination to Spanish.

## Key Decisions

1. **Used `call_llm` (OpenAI-compatible client) instead of `call_gemma`** — The codebase has two LLM clients. `gemma_client.py` references `settings.GEMMA_API_KEY` which doesn't exist in config; `llm_client.py` uses `settings.LLM_API_KEY` which is the correct one. The existing tests mock `call_llm`.
2. **Prompt returns JSON with `decision` field** — Since `call_llm` doesn't force `responseMimeType: application/json`, the prompt asks the LLM to respond as `{"decision": "..."}`. If the LLM returns plain text instead, it's used directly. The API response also includes a predefined short justification (<=25 words).
3. **ChartWithInsight wrapper** — Rather than modifying each of the 9 chart components, a wrapper in App.jsx renders the chart and its insight together. This keeps chart components unchanged and the integration centralized.
4. **Skeleton uses Tailwind `animate-pulse`** — Three gray bars with pulse animation. No custom CSS needed.
5. **Domain context per chart** — Each chart type maps to its "Decision it improves" and "Justification" from docs/domain.md, included in the LLM prompt.

## Notes for Reviewer

- The `gemma_client.py` has a pre-existing bug: it references `settings.GEMMA_API_KEY` but the config only defines `LLM_API_KEY`. This is not introduced by this feature — it's a pre-existing issue. The insight endpoint correctly uses `llm_client.py`.
- Frontend build was tested with `docker compose build --no-cache` and passes.
- All 135 tests pass (125 existing + 10 new insight tests).
