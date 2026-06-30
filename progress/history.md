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
