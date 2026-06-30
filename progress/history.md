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
