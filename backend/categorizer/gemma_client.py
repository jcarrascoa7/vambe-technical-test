"""Async HTTP client for Gemma 4 API using httpx."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

# Gemma 4 API uses this payload structure
# https://ai.google.dev/api/generate-content


def _build_payload(prompt: str) -> dict[str, Any]:
    """Build the request payload for Gemma 4 generateContent endpoint."""
    return {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }


async def call_gemma(
    prompt: str,
    *,
    max_retries: int = 3,
    timeout: float = 30.0,
) -> str:
    """Call the Gemma 4 API with a prompt and return the response text.

    Retries with exponential backoff on transient failures (timeout, connection
    errors, 5xx status codes). Returns an empty string on permanent failures
    (malformed response, missing content) rather than raising — the caller
    decides what to do with an empty result.

    Args:
        prompt: The prompt text to send.
        max_retries: Number of retry attempts for transient failures.
        timeout: Per-request timeout in seconds.

    Returns:
        The response text from the API, or empty string on failure.
    """
    api_key = settings.GEMMA_API_KEY
    api_url = settings.GEMMA_API_URL

    if not api_key:
        logger.error("GEMMA_API_KEY is not set")
        return ""

    url = f"{api_url}?key={api_key}"
    payload = _build_payload(prompt)

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=timeout,
                )

            if response.status_code >= 500:
                logger.warning(
                    "Gemma API server error %d (attempt %d/%d)",
                    response.status_code,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(2**attempt)
                continue

            if response.status_code != 200:
                logger.error(
                    "Gemma API returned status %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return ""

            data = response.json()

        except httpx.TimeoutException:
            logger.warning(
                "Gemma API timeout (attempt %d/%d)", attempt + 1, max_retries
            )
            await asyncio.sleep(2**attempt)
            continue

        except httpx.HTTPError as exc:
            logger.warning(
                "Gemma API connection error (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                exc,
            )
            await asyncio.sleep(2**attempt)
            continue

        except (ValueError, KeyError):
            # Malformed JSON or unexpected structure
            logger.error("Malformed response from Gemma API")
            return ""

        # Extract text from response
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                logger.warning("Gemma API returned no candidates")
                return ""

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                logger.warning("Gemma API returned empty parts")
                return ""

            return parts[0].get("text", "")

        except (KeyError, IndexError, TypeError):
            logger.error("Unexpected Gemma API response structure")
            return ""

    logger.error("Gemma API failed after %d retries", max_retries)
    return ""
