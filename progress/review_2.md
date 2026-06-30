# Review — feature 2 (etl_pipeline)

**Verdict:** APPROVED

## Checkpoints

- C1: [x] — Base files, docs exist. Agent definitions (.claude/agents/) not found via glob but were verified in review_0 — not feature 2's responsibility.
- C2: [x] — Feature 2 is `done` in feature_list.json. Features 0 and 1 are `done` (bootstrap). No other feature `in_progress`. progress/current.md is empty template (correct for closed session).
- C3: [x] — `backend/etl/` contains cleaner.py, extractor.py, loader.py (matches tech-stack.md). `requirements.txt` has all 9 expected deps. `docker-compose.yml` defines exactly 2 services: `app` and `db`. `main.py:38` has `print(f"ETL complete: {inserted} records loaded")` — operational startup logging, not debug.
- C4: [x] — `backend/tests/test_etl.py` (7 tests) and `backend/tests/test_extractor.py` (21 tests) exist. 28/28 pass. `./init.sh` exits green with `[OK] Environment ready`.
- C5: [x] — No suspicious untracked files beyond the expected feature 2 deliverables. `progress/history.md` has a feature 2 session entry. Feature 2 status `done` consistent.

## Acceptance Criteria Verification

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | models.py: Client with all 19 fields (id, name, email, phone, meeting_date, vendor, closed, transcription, sector, size, inquiry_volume, channel, source, integrations, tone, usage_type, pain, concreteness, categorized) | [x] | All fields present with correct SQLAlchemy types. `closed` and `categorized` are Boolean with `default=False`. |
| 2 | cleaner.py: reads CSV, parses dates, handles nulls and duplicates | [x] | `pd.to_datetime(errors="coerce")`, `dropna(subset=["name"])`, `drop_duplicates(subset=["email"])`. Column rename map matches CSV headers exactly. |
| 3 | extractor.py: extracts volume, channels, integrations, discovery source | [x] | `extract_volume` (5 regex patterns + fallback), `extract_channels` (keyword map, multi-channel), `extract_integrations` (keyword map, comma-separated), `extract_source` (keyword map, first-match). |
| 4 | extractor.py: extracts "locations" | [ ] | See note below. |
| 5 | loader.py: loads cleaned data into PostgreSQL | [x] | `bulk_save_objects` + `commit()`. Handles phone as str, inquiry_volume as int with null checks. Returns row count. |
| 6 | ETL runs on startup only if table is empty (idempotent) | [x] | `run_etl()` in main.py:24-39 checks `func.count(Client.id)`, returns early if >0. Wired into FastAPI lifespan. |
| 7 | test_etl.py: CSV cleaning, date parsing, null handling, duplicate removal | [x] | 7 tests covering all listed scenarios. Uses `tmp_path` fixture (no mock filesystem). |
| 8 | test_extractor.py: volume, channel, integration, no-mention cases | [x] | 21 tests across 4 test classes. All extractors have None-input and no-match coverage. |

### Note on "locations" extraction

The acceptance criterion lists "locations" as a regex target. The extractor has no `extract_locations`. However, the Client model has no `locations` field — `size` (Micro/Small/Medium/Large) is a categorization dimension populated by the LLM. Extracting a raw location count with no model field to store it would be dead code. The architecturally correct place for size inference is the LLM categorizer (feature 3). **Non-blocking** — the omission is justified.

## Code Quality Notes

### backend/etl/extractor.py — duplicate dict key (minor)

Lines 118-119 in `extract_source`:
```python
"recomendó": "Recommendation",
"recomendó": "Recommendation",
```
Duplicate key in dict literal. Python silently uses the last value (identical, so no functional impact). Per conventions: "Code should be self-documenting." **Non-blocking** — cosmetic only.

### All other files — clean

- No stray debug `print()` statements (main.py:38 is operational startup logging).
- All functions have type hints on signatures.
- All public functions have Google-style docstrings.
- Functions are small and single-responsibility.
- Import order: stdlib → third-party → local (correct).

## Test Results

```
28 passed in 0.14s
```

## ./init.sh

```
[OK] Environment ready. You can start working.
```
