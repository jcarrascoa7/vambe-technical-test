# Session History

Append-only log of completed sessions.

---

## Session: 2026-06-29 — Feature 0: bootstrap

**Status**: done
**Plan**:
1. Create backend skeleton: main.py, config.py, database.py, models.py, requirements.txt, tests/__init__.py
2. Create frontend skeleton: React+Vite app with package.json
3. Create docker-compose.yml (app + db services) and Dockerfile (multi-stage: Node build + Python)
4. Run ./init.sh to verify all checks pass

**Notes**: Building the foundation for all other features.

---

## Session: 2026-06-29 — Feature 2: etl_pipeline

**Status**: done
**Plan**:
1. Define full Client model in models.py
2. Implement cleaner.py (CSV read, date parse, nulls, dedup)
3. Implement extractor.py (regex for volume, channels, integrations, source)
4. Implement loader.py (load to PostgreSQL)
5. Wire ETL into main.py startup (idempotent)
6. Write test_etl.py and test_extractor.py
7. Run ./init.sh until green

**Notes**: ETL pipeline reads CSV, cleans with pandas, extracts signals via regex, loads into PostgreSQL. Runs idempotently on startup if table is empty.

---

## Session: 2026-06-29 — Refactor: Remove regex extractor, delegate all categorization to LLM

**Status**: done
**Reason**: The technical test spec says "Utiliza algún modelo de lenguaje como Gemma 4 para automatizar la categorización". The regex extractor was over-engineering not requested by the spec. ALL dimensions (including volume, channel, source, integrations) should be categorized by the LLM.

**Changes**:
1. Deleted `backend/etl/extractor.py` and `backend/tests/test_extractor.py`
2. Simplified `backend/main.py` — removed extractor imports and calls
3. Simplified `backend/etl/loader.py` — only loads CSV fields, categorization fields left as NULL for LLM
4. Updated `feature_list.json` — removed regex acceptance criteria from feature 2, added "ALL dimensions via LLM" to feature 3
5. Updated docs: `architecture.md`, `tech-stack.md`, `verification.md`, `CHECKPOINTS.md`, `AGENTS.md`

**Architecture after change**: ETL only cleans CSV → DB. LLM categorizer handles ALL 10 dimensions.

---

## Session: 2026-06-29 — Feature 3: categorizer_prompts_validator

**Status**: done
**Plan**:
1. Implement prompts.py: build_categorization_prompt with schema + few-shot examples for all 10 dimensions
2. Implement validator.py: validate_response against predefined category lists from domain.md, map invalid to 'Otros'
3. Implement test_categorizer.py: valid passes, invalid mapped, malformed JSON, empty response
4. Run ./init.sh until green

**Notes**: All 10 dimensions extracted by LLM only (no regex). Valid categories per domain.md; 'Other'/'Otros' is the fallback for unknown values. inquiry_volume stored as Integer in DB but LLM returns categorical bucket.

---

## Session: 2026-06-29 — Feature 4: categorizer_client

**Status**: done
**Plan**:
1. Implement gemma_client.py: async httpx client with retry + timeout
2. Implement test_gemma_client.py: cover success, timeout, malformed JSON, empty response, retry logic
3. Run ./init.sh until green

**Notes**: Async HTTP client for Gemma 4 API using httpx. Handles retries, timeouts, and malformed JSON responses gracefully.

---

## Session: 2026-06-30 — Refinements: prompts, validator, model config

**Status**: done
**What was done** (no single feature, multiple refinements across existing code):

### 1. Enriched LLM prompt with dimension definitions
- Added `DIMENSION_DEFINITIONS` block to `backend/categorizer/prompts.py` with detailed criteria for:
  - **size**: Micro (1 location, <10 employees), Small (2-3), Medium (4-10), Large (10+)
  - **inquiry_volume**: Low (<500/month), Medium (500-2k), High (2k-5k), Very High (>5k)
  - **concreteness**: Concrete/Actionable vs Tentative/Exploratory vs Mixed
  - **pain**: disambiguation for each category
- Added reasoning section to few-shot example
- Fixed bug: few-shot example had "3 sedes" → Medium (wrong), changed to Small

### 2. "Not specified" fallback instead of fake data
- Added "Not specified" to `VALID_CATEGORIES` for: size, inquiry_volume, concreteness
- Changed `validate_category()` fallbacks: "Micro"/"Medium" → "Not specified" for size/inquiry_volume
- Old fallbacks polluted metrics with fake data; "Not specified" can be filtered out in dashboard

### 3. inquiry_volume: Integer → String in DB
- Changed `models.py`: `inquiry_volume = Column(String(50))` (was `Integer`)
- Removed int conversion from `validator.py` — stores bucket string like all other dimensions
- `INQUIRY_VOLUME_MAP` kept in `prompts.py` for API-layer metric calculations (avg volume by sector)
- No NULLs in any categorization column — all are strings, "Not specified" is the fallback

### 4. Data Exclusion Rule in docs
- Added "Data Exclusion Rule" section to `docs/domain.md` under Metrics
- Rule: records with "Not specified" in a dimension are excluded from metrics depending on that dimension
- Added acceptance criterion to feature 7 in `feature_list.json`

### 5. Model config and LLM connectivity
- Updated `.env.example` and `AGENTS.md`: model URL now `gemma-4-26b-a4b-it`
- Created `backend/test_llm_connection.py` — smoke test for Gemma API
- Added `responseMimeType: "application/json"` to `gemma_client.py` payload

### 6. Robust JSON parser
- `parse_llm_response()` in `validator.py` now extracts JSON from mixed content (LLM reasoning + JSON)
- Uses regex to find last `{...}` block when direct parse fails
- gemma-4-26b-a4b-it tends to add reasoning text before JSON; parser handles this gracefully

**Files modified**:
- `backend/categorizer/prompts.py` — dimension definitions, "Not specified" categories, INQUIRY_VOLUME_MAP comment
- `backend/categorizer/validator.py` — "Not specified" fallbacks, robust JSON extraction, removed int conversion
- `backend/categorizer/gemma_client.py` — responseMimeType in payload
- `backend/models.py` — inquiry_volume String(50)
- `backend/test_llm_connection.py` — new file
- `.env.example` — correct model URL
- `AGENTS.md` — correct model URL
- `docs/domain.md` — Data Exclusion Rule
- `feature_list.json` — exclusion acceptance criterion, NULL references cleaned
- `backend/tests/test_categorizer.py` — updated tests for new fallbacks and string inquiry_volume

**Tests**: 48/48 passing

---

## Session: 2026-06-30 — Feature 5: categorizer_processor

**Status**: done
**Plan**:
1. Implement processor.py: async batch loop (50 records), mark categorized=true, resume support
2. Implement test_processor.py: batch processing, flag update, resume after restart, empty table
3. Wire processor into main.py lifespan as background task
4. Run ./init.sh until green

**Key decisions**:
- Used `asyncio.sleep` between batches for non-blocking background processing
- Processor queries `WHERE categorized = false` for resume support
- Wired into FastAPI lifespan with `asyncio.create_task` so it doesn't block startup
- Batch size configurable via `BATCH_SIZE` constant (default 50)
- Categorized flag set to `true` per record immediately after categorization (not batch-level)

**Files modified**:
- `backend/categorizer/processor.py` — new file (batch processor)
- `backend/categorizer/__init__.py` — updated exports
- `backend/main.py` — wired processor into lifespan as background task
- `backend/tests/test_processor.py` — new file (4 tests)

**Tests**: 52/52 passing

---

## Session: 2026-06-30 — Feature 6: api_clients_endpoints

**Status**: done
**Plan**:
1. Create backend/api/schemas.py with Pydantic v2 response schemas
2. Create backend/api/routes/clients.py with GET /clients endpoint
3. Register the router in backend/main.py
4. Write backend/tests/test_schemas.py for schema validation
5. Write backend/tests/test_api_clients.py for endpoint tests

**Key decisions**:
- Used Pydantic v2 with model_config for ORM mode serialization
- Implemented filter logic with SQLAlchemy dynamic query building
- Search across name and email using ilike for case-insensitive matching
- Pagination via limit/offset with total count in response
- Status endpoint returns categorization progress metrics

**Files modified**:
- backend/api/schemas.py — new file (Pydantic v2 schemas)
- backend/api/routes/clients.py — new file (GET /clients with filters, search, pagination)
- backend/api/__init__.py — new file (package init)
- backend/api/routes/__init__.py — new file (package init)
- backend/main.py — registered clients router
- backend/tests/test_schemas.py — new file (schema validation tests)
- backend/tests/test_api_clients.py — new file (endpoint tests)

**Tests**: All passing

---

## Session: 2026-06-30 — Feature 7: api_metrics_endpoints

**Status**: done
**Plan**:
1. Create backend/api/routes/metrics.py with all 12 metric endpoints
2. Register metrics router in main.py
3. Write backend/tests/test_api_metrics.py covering all endpoints + zero records edge case
4. Run ./init.sh until green

**Key decisions**:
- All metrics query only categorized records (WHERE categorized = true)
- "Not specified" values excluded per Data Exclusion Rule from domain.md
- INQUIRY_VOLUME_MAP used for converting bucket strings to numeric for avg calculations
- Heatmap endpoint returns nested dict structure (vendor → sector → rate)
- Temporal evolution groups by year-month string for Chart.js compatibility

**Files modified**:
- backend/api/routes/metrics.py — new file (12 metric endpoints)
- backend/main.py — registered metrics router
- backend/tests/test_api_metrics.py — new file (all endpoints + edge cases)

**Tests**: All passing

---

## Session: 2026-06-30 — Feature 8: dashboard_filters

**Status**: done
**Plan**:
1. Install Tailwind CSS in frontend
2. Create api/client.js fetch wrapper
3. Create hooks/useFilters.js custom hook
4. Create components/Filters.jsx panel
5. Update App.jsx to wire filters + basic layout
6. Run ./init.sh to verify build

**Key decisions**:
- Tailwind CSS via @tailwindcss/vite plugin (zero config)
- useFilters hook manages filter state and derives apiParams
- Filters passed as query params to /clients endpoint
- Memoized apiParams with useMemo to prevent infinite re-fetch loop
- Basic table layout for client list with filter panel

**Files modified**:
- frontend/package.json — added tailwindcss, @tailwindcss/vite
- frontend/vite.config.js — added tailwind plugin
- frontend/src/index.css — @import "tailwindcss"
- frontend/src/api/client.js — new file (fetch wrapper)
- frontend/src/hooks/useFilters.js — new file (filter state + apiParams)
- frontend/src/components/Filters.jsx — new file (filter panel UI)
- frontend/src/App.jsx — wired filters, table, status

**Tests**: ./init.sh green

---

## Session: 2026-06-30 — Feature 9: dashboard_kpi_cards

**Status**: done
**Plan**:
1. Create KPICards component with total leads, overall close rate, top sector, top vendor
2. Compute KPIs client-side from close-rate-by-sector and close-rate-by-vendor-sector endpoints
3. Wire into App.jsx, pass apiParams so cards update with filters
4. Build frontend, run init.sh

**Key decisions**:
- KPI cards compute derived metrics client-side from existing metric endpoints (no new backend endpoints)
- Total leads from /clients count, close rate from /metrics/close-rate-by-sector, top sector/vendor from aggregations
- Cards update reactively when filters change via apiParams dependency
- Styled with Tailwind gradient cards for visual hierarchy

**Files modified**:
- frontend/src/components/KPICards.jsx — new file (KPI cards component)
- frontend/src/App.jsx — integrated KPICards with apiParams

**Tests**: ./init.sh green

---

## Session: 2026-06-30 — Feature 10: dashboard_client_table

**Status**: done
**Plan**:
1. Extract client table from App.jsx into ClientTable.jsx with search + pagination
2. Add categorization progress bar component
3. Wire into App.jsx, verify build

**Key decisions**:
- Search: form-based submit (Enter or button), not debounced — simpler, no extra deps
- Pagination: client-managed offset state, PAGE_LIMIT=20 rows per page
- Progress bar: Tailwind-only, no Chart.js needed; polls `/clients/status` every 10s
- No new dependencies: all done with React useState/useCallback + Tailwind classes

**Files modified**:
- `frontend/src/App.jsx` — extracted table into ClientTable component, added search/pagination state, added CategorizationProgress component with progress bar and 10s polling
- `frontend/src/components/ClientTable.jsx` — new component: search input by name/email, paginated table with Previous/Next buttons and page indicator

**Notes**: Backend already supported `search`, `limit`, `offset` params — no backend changes needed. `fetchStatus` already existed in `api/client.js`. Progress bar shows blue during processing, green when complete.

---

## Session: 2026-06-30 — Feature 11: dashboard_charts_basic

**Status**: done
**Plan**:
1. Install chart.js + react-chartjs-2
2. Create CloseRateBySector chart (bar, sorted descending)
3. Create SectorDistribution chart (donut)
4. Create PainDistribution chart (100% stacked bar)
5. Create CloseRateBySource chart (bar + global avg reference line)
6. Create CloseRateByConcreteness chart (bar + highlighted gap)
7. Wire charts into App.jsx, make them respond to filter changes
8. Fix close-rate-by-source endpoint to accept filters
9. Run ./init.sh until green

**Key decisions**:
- Used chartjs-plugin-annotation for the global average reference line on CloseRateBySource
- PainDistribution computes percentages client-side for 100% stacked bars
- CloseRateByConcreteness colors highest green, lowest red, others blue to highlight the gap
- All charts receive `apiParams` from useFilters hook — filter changes trigger re-fetch via useEffect dependency
- All 5 chart-related API endpoints now accept the same filter params as close-rate-by-sector

**Files modified**:
- `frontend/package.json` — added chart.js, react-chartjs-2, chartjs-plugin-annotation
- `frontend/src/App.jsx` — imported and rendered 5 chart components in grid layout
- `frontend/src/components/Charts/CloseRateBySector.jsx` — new: horizontal bar chart, sorted descending
- `frontend/src/components/Charts/SectorDistribution.jsx` — new: donut chart with 17-color palette
- `frontend/src/components/Charts/PainDistribution.jsx` — new: 100% stacked bar chart
- `frontend/src/components/Charts/CloseRateBySource.jsx` — new: bar chart with global avg reference line
- `frontend/src/components/Charts/CloseRateByConcreteness.jsx` — new: bar chart with color-coded gap highlight
- `backend/api/routes/metrics.py` — added filter params to 4 endpoints
- `backend/tests/test_api_metrics.py` — added filter acceptance tests

**Tests**: ./init.sh green

---

## Session: 2026-06-30 — Feature 12: dashboard_charts_advanced

**Status**: done
**Plan**:
1. Create VendorSectorHeatmap component (HTML table with color-coded cells, no extra deps)
2. Create TemporalEvolution component (dual Line chart)
3. Create IntegrationsDistribution component (horizontal Bar chart)
4. Create VolumeCloseRateScatter component (Scatter chart with labeled points)
5. Wire all 4 into App.jsx grid
6. Verify with ./init.sh

**Key decisions**:
- Heatmap uses CSS grid/table (Chart.js has no native heatmap; avoids adding chartjs-chart-matrix dep)
- All backend endpoints already existed from features 7 and 11 — no backend changes needed
- All 4 advanced charts receive `apiParams` from useFilters hook — filter changes trigger re-fetch

**Files modified**:
- `frontend/src/components/Charts/VendorSectorHeatmap.jsx` — new: HTML table with color-coded cells for vendor × sector close rates
- `frontend/src/components/Charts/TemporalEvolution.jsx` — new: dual Line chart for leads and closes over time (monthly)
- `frontend/src/components/Charts/IntegrationsDistribution.jsx` — new: horizontal Bar chart for top requested integrations
- `frontend/src/components/Charts/VolumeCloseRateScatter.jsx` — new: Scatter chart with labeled points for volume × close rate by sector
- `frontend/src/App.jsx` — imported and rendered all 4 advanced chart components in grid layout

**Tests**: ./init.sh green

---

## Session: 2026-06-30 — Feature 13: ci_cd_pipeline

**Status**: done
**Plan**:
1. Create .github/workflows/ci.yml with lint, Docker build, pytest, frontend build
2. Create .github/workflows/deploy.yml placeholder for Railway
3. Add eslint + prettier to frontend for CI linting
4. Add ruff + black to backend requirements
5. Run ./init.sh until green

**Key decisions**:
- Node.js copied from frontend-build stage in Dockerfile for CI frontend builds (~30MB overhead)
- Ruff + Black run on GitHub Actions runner (fast, no Docker); tests run inside Docker (matches production)
- ESLint + Prettier added as frontend devDeps with lint/format:check scripts
- E712 ignored in ruff (SQLAlchemy `Column == True` is idiomatic)
- E501 ignored in ruff (Black handles line length)
- Deploy workflow: placeholder with echo; real Railway integration needs CLI or webhook
- Fail-fast: each step sequential, any failure stops workflow

**Files modified**:
- `.github/workflows/ci.yml` — new: CI workflow
- `.github/workflows/deploy.yml` — new: deploy placeholder
- `Dockerfile` — added Node.js + npm to final stage
- `frontend/package.json` — added eslint, prettier, scripts
- `frontend/.eslintrc.cjs` — new: ESLint config
- `backend/requirements.txt` — added ruff, black
- `pyproject.toml` — new: ruff config
- Multiple backend/frontend files — lint/format fixes

**Tests**: 124/124 passing

---

## Session: 2026-06-30 — LLM Switch: Gemma → Xiaomi MiMo + UI Fixes

**Status**: done
**Plan**:
1. Replace gemma_client.py with llm_client.py (OpenAI-compatible format)
2. Rename GEMMA_* env vars to LLM_*
3. Fix frontend caching issue (frontend_dist named volume)
4. Add logging for categorization progress
5. Reduce batch size for faster visible progress
6. Create PR with all changes

**Key decisions**:
- Xiaomi MiMo uses OpenAI-compatible API (`POST /chat/completions` with `Authorization: Bearer`)
- Removed `frontend_dist` named volume from docker-compose.yml — was caching old JS builds across rebuilds
- Added `logging.basicConfig` in main.py so categorizer logs appear in `docker compose logs`
- Batch size reduced from 50 to 20 for faster visible progress in dashboard
- MAX_RECORDS_TO_CATEGORIZE set to 100 (user's API key has usage limits)
- Added `/api` prefix to routers, then reverted — new frontend uses paths without prefix

**Files modified**:
- `backend/categorizer/llm_client.py` — new: OpenAI-compatible LLM client
- `backend/categorizer/processor.py` — import llm_client, BATCH_SIZE=20
- `backend/config.py` — renamed GEMMA_* to LLM_*, default model mimo-v2.5-pro
- `backend/main.py` — added logging.basicConfig
- `.env.example` — updated var names and Xiaomi API URL
- `AGENTS.md` — updated env var table
- `docker-compose.yml` — removed frontend_dist named volume
- `backend/tests/test_llm_client.py` — new: tests for llm_client
- `backend/tests/test_gemma_client.py` — deleted
- `backend/test_llm_connection.py` — updated imports
- `backend/test_categorization.py` — updated imports

**Tests**: 125/125 passing

---

## Session: 2026-06-30 — Feature 14: chart_insights_llm

**Status**: done
**Plan**:
1. Create backend/api/insights.py with GET /insights/{chart_type} endpoint using existing llm_client
2. Write backend/tests/test_insights.py (success, LLM failure fallback, all chart types)
3. Add fetchInsight to frontend/src/api/client.js
4. Create frontend/src/components/ChartInsight.jsx (reusable with skeleton + text states)
5. Integrate ChartInsight into each chart component in App.jsx
6. Localize all frontend UI text to Spanish (title, KPIs, filters, table headers, buttons)
7. Expand ClientTable to show all categorized dimensions + transcription
8. Run ./init.sh until green

**Key decisions**:
- Used `call_llm` (OpenAI-compatible client) — `gemma_client.py` has a pre-existing bug referencing `settings.GEMMA_API_KEY` which doesn't exist in config
- Prompt returns JSON with `decision` field; if LLM returns plain text instead, it's used directly
- ChartWithInsight wrapper in App.jsx renders chart + insight together — keeps chart components unchanged
- Skeleton uses Tailwind `animate-pulse` (three gray bars), no custom CSS
- Domain context per chart maps to "Decision it improves" and "Justification" from docs/domain.md

**Files modified**:
- `backend/api/insights.py` — new: GET /insights/{chart_type} endpoint
- `backend/main.py` — registered insights_router
- `backend/tests/test_insights.py` — new: 10 tests (success, fallbacks, chart types, justification word limit)
- `frontend/src/api/client.js` — added fetchInsight(chartType)
- `frontend/src/components/ChartInsight.jsx` — new: reusable skeleton + text component
- `frontend/src/App.jsx` — title localized, ChartWithInsight wrapper, CategorizationProgress in Spanish
- `frontend/src/components/KPICards.jsx` — labels localized to Spanish
- `frontend/src/components/Filters.jsx` — labels localized to Spanish
- `frontend/src/components/ClientTable.jsx` — expanded with all dimensions + transcription, localized

**Tests**: 135/135 passing (125 existing + 10 new insight tests)

---

## Session: 2026-06-30 — Feature 15: integration_and_polish

**Status**: done
**Plan**:
1. Read docs/architecture.md, docs/tech-stack.md, docs/domain.md to understand system
2. Check existing codebase for debug prints, TODOs, temp files
3. Write README.md in Spanish with all required sections
4. Write integration test (no debug prints verification)
5. Fix debug print in backend/main.py → logging.info
6. Run ./init.sh until green
7. Write progress/impl_integration_and_polish.md

**Key decisions**:
- Fixed debug `print()` in `backend/main.py` → replaced with `logger.info()` (logging module was already imported)
- `backend/test_categorization.py` and `backend/test_llm_connection.py` have prints but they are standalone diagnostic scripts, not production code — left as-is
- No TODOs without context found in codebase
- No temp files found
- README.md written entirely in Spanish with all required sections: setup instructions, architecture docs, stack description, LLM configuration, key decisions (discarded dimensions, LLM consistency techniques, stack justification), repo link, deploy placeholder

**Files modified**:
- `backend/main.py` — replaced `print()` with `logger.info()`
- `README.md` — full rewrite in Spanish
- `backend/tests/test_integration.py` — new: AST-based verification of no debug prints in production modules
- `progress/impl_integration_and_polish.md` — implementation summary

**Tests**: All passing (./init.sh green)
