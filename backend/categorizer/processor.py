"""Batch orchestration for categorizing client records with the LLM."""

from __future__ import annotations

import asyncio
import logging
from typing import Callable

from sqlalchemy import update
from sqlalchemy.orm import Session

from backend.categorizer.gemma_client import call_gemma
from backend.categorizer.prompts import build_categorization_prompt
from backend.categorizer.validator import validate_response
from backend.config import settings
from backend.database import SessionLocal
from backend.models import Client

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


def _get_uncategorized_batch(db: Session, batch_size: int) -> list[Client]:
    """Fetch a batch of uncategorized clients."""
    return (
        db.query(Client)
        .filter(Client.categorized == False)  # noqa: E712
        .limit(batch_size)
        .all()
    )


def _mark_categorized(db: Session, client_ids: list[int]) -> None:
    """Mark a list of client IDs as categorized."""
    if not client_ids:
        return
    db.execute(
        update(Client).where(Client.id.in_(client_ids)).values(categorized=True)
    )
    db.commit()


async def _categorize_client(client: Client) -> dict | None:
    """Categorize a single client record via the LLM.

    Returns the validated categorization dict, or None on failure.
    """
    if not client.transcription:
        return None

    prompt = build_categorization_prompt(client.transcription)
    raw_response = await call_gemma(prompt)

    if not raw_response:
        return None

    return validate_response(raw_response)


def _apply_categorization(client: Client, categories: dict) -> None:
    """Apply validated categories to a client record."""
    for dim, value in categories.items():
        setattr(client, dim, value)


async def process_batch(
    db: Session,
    categorize_fn: Callable = _categorize_client,
) -> int:
    """Process one batch of uncategorized records.

    Returns the number of successfully categorized records.
    """
    clients = _get_uncategorized_batch(db, BATCH_SIZE)
    if not clients:
        return 0

    categorized_ids: list[int] = []
    for client in clients:
        categories = await categorize_fn(client)
        if categories:
            _apply_categorization(client, categories)
            categorized_ids.append(client.id)

    _mark_categorized(db, categorized_ids)
    return len(categorized_ids)


async def run_categorization(
    max_records: int | None = None,
    categorize_fn: Callable = _categorize_client,
) -> None:
    """Run categorization on all uncategorized records in batches.

    Processes up to max_records (defaults to MAX_RECORDS_TO_CATEGORIZE).
    Only processes WHERE categorized = false, so restarting picks up where
    it left off. Runs in background — does not block the event loop between
    batches (await asyncio.sleep(0) yields control).
    """
    if max_records is None:
        max_records = settings.MAX_RECORDS_TO_CATEGORIZE

    processed = 0
    while processed < max_records:
        db = SessionLocal()
        try:
            count = await process_batch(db, categorize_fn)
        finally:
            db.close()

        if count == 0:
            logger.info("No more uncategorized records. Done.")
            break

        processed += count
        logger.info("Categorized %d records (total: %d/%d)", count, processed, max_records)

        # Yield control to the event loop so API remains responsive
        await asyncio.sleep(0)

    logger.info("Categorization complete: %d records processed.", processed)
