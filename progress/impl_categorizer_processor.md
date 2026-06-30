# Implementation Summary — Feature 5: Categorizer Batch Processor

## Files Modified

- **backend/categorizer/processor.py** (new) — Batch orchestration module
- **backend/main.py** — Wired processor as background task in lifespan
- **backend/tests/test_processor.py** (new) — 14 tests covering all acceptance criteria

## Key Decisions

1. **Batch size = 50** as a module constant, matching the acceptance criteria
2. **Async throughout**: `process_batch` and `run_categorization` are async to allow the LLM calls (httpx async) to yield control between batches via `asyncio.sleep(0)`
3. **New session per batch**: Each batch gets its own `SessionLocal()` to avoid long-lived connections and support clean resume
4. **Background via `asyncio.create_task`**: Categorization runs in a background task that doesn't block the API or dashboard. Task is cancelled on shutdown
5. **Injectable `categorize_fn`**: Tests pass a mock instead of calling the real LLM
6. **`_has_uncategorized_records()` guard**: Only starts the background task if there are uncategorized records, avoiding unnecessary work on restarts when everything is already done

## Acceptance Criteria Coverage

| Criterion | How |
|---|---|
| Process batches of 50 | `BATCH_SIZE = 50`, `_get_uncategorized_batch` uses `.limit(batch_size)` |
| Mark categorized=true after each batch | `_mark_categorized` commits after each batch |
| WHERE categorized = false | All queries filter `Client.categorized == False` |
| Resume on restart | Query always starts from `categorized=false`, so restart picks up where left off |
| Background doesn't block API | `asyncio.create_task` + `asyncio.sleep(0)` yields control between batches |
| Tests cover batch processing | `test_process_batch_categorizes_records` |
| Tests cover categorized flag | `TestMarkCategorized` (3 tests) + `test_process_batch_skips_failed_records` |
| Tests cover resume | `test_run_categorization_resumes_on_restart` |
| Tests cover empty table | `test_run_categorization_empty_table`, `TestGetUncategorizedBatch::test_empty_table_returns_empty` |
