"""Async HTTP client for LLM API (OpenAI-compatible format)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


def _build_payload(prompt: str) -> dict[str, Any]:
    """Build the request payload for an OpenAI-compatible chat endpoint."""
    return {
        "model": settings.LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 4096,
    }


async def call_llm(
    prompt: str,
    *,
    max_retries: int = 3,
    timeout: float = 90.0,
) -> str:
    """Call an OpenAI-compatible LLM API with a prompt and return the response text.

    Retries with exponential backoff on transient failures (timeout, connection
    errors, 5xx status codes). Returns an empty string on permanent failures
    rather than raising — the caller decides what to do with an empty result.
    """
    api_key = settings.LLM_API_KEY

    if not api_key:
        logger.error("LLM_API_KEY is not set")
        return ""

    url = f"{settings.LLM_API_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = _build_payload(prompt)

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )

            if response.status_code >= 500:
                logger.warning(
                    "LLM API server error %d (attempt %d/%d)",
                    response.status_code,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(2**attempt)
                continue

            if response.status_code != 200:
                logger.error(
                    "LLM API returned status %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return ""

            data = response.json()

        except httpx.TimeoutException:
            logger.warning(
                "LLM API timeout (attempt %d/%d)", attempt + 1, max_retries
            )
            await asyncio.sleep(2**attempt)
            continue

        except httpx.HTTPError as exc:
            logger.warning(
                "LLM API connection error (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                exc,
            )
            await asyncio.sleep(2**attempt)
            continue

        except (ValueError, KeyError):
            logger.error("Malformed response from LLM API")
            return ""

        # Extract text from OpenAI-compatible response
        try:
            choices = data.get("choices", [])
            if not choices:
                logger.warning("LLM API returned no choices")
                return ""

            return choices[0].get("message", {}).get("content", "")

        except (KeyError, IndexError, TypeError):
            logger.error("Unexpected LLM API response structure")
            return ""

    logger.error("LLM API failed after %d retries", max_retries)
    return ""
