"""Tests for the Gemma 4 async HTTP client."""

from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from backend.categorizer.gemma_client import _build_payload, call_gemma


# --- helpers ---


def _gemma_response(text: str) -> dict:
    """Build a minimal valid Gemma API response body."""
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def _ok_response(body: dict) -> httpx.Response:
    """Build a 200 httpx.Response with JSON body."""
    return httpx.Response(200, json=body, request=httpx.Request("POST", "https://x"))


def _error_response(status: int) -> httpx.Response:
    """Build an error httpx.Response."""
    return httpx.Response(status, request=httpx.Request("POST", "https://x"))


async def _noop_sleep(_: float) -> None:
    """Replacement for asyncio.sleep in tests."""


# --- _build_payload ---


class TestBuildPayload:
    def test_contains_prompt(self):
        payload = _build_payload("hello")
        assert payload["contents"][0]["parts"][0]["text"] == "hello"

    def test_temperature_zero(self):
        payload = _build_payload("test")
        assert payload["generationConfig"]["temperature"] == 0


# --- call_gemma ---


@pytest.mark.asyncio
async def test_successful_call(monkeypatch):
    """Happy path: API returns valid JSON with text content."""
    expected = '{"sector": "Health"}'
    fake_client = AsyncMock()
    fake_client.post.return_value = _ok_response(_gemma_response(expected))
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(
        "backend.categorizer.gemma_client.httpx.AsyncClient",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        "backend.categorizer.gemma_client.settings.GEMMA_API_KEY", "test-key"
    )

    result = await call_gemma("prompt")
    assert result == expected


@pytest.mark.asyncio
async def test_timeout_returns_empty(monkeypatch):
    """Timeout after all retries returns empty string."""
    fake_client = AsyncMock()
    fake_client.post.side_effect = httpx.TimeoutException("timed out")
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(
        "backend.categorizer.gemma_client.httpx.AsyncClient",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        "backend.categorizer.gemma_client.settings.GEMMA_API_KEY", "test-key"
    )
    monkeypatch.setattr("backend.categorizer.gemma_client.asyncio.sleep", _noop_sleep)

    result = await call_gemma("prompt", max_retries=2)
    assert result == ""
    assert fake_client.post.call_count == 2


@pytest.mark.asyncio
async def test_malformed_json_returns_empty(monkeypatch):
    """Non-JSON body in a 200 response returns empty string."""
    # Build a response whose content is not valid JSON
    resp = httpx.Response(200, request=httpx.Request("POST", "https://x"))
    resp._content = b"not json"

    fake_client = AsyncMock()
    fake_client.post.return_value = resp
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(
        "backend.categorizer.gemma_client.httpx.AsyncClient",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        "backend.categorizer.gemma_client.settings.GEMMA_API_KEY", "test-key"
    )

    result = await call_gemma("prompt", max_retries=1)
    assert result == ""


@pytest.mark.asyncio
async def test_empty_candidates_returns_empty(monkeypatch):
    """API returns 200 but with empty candidates list."""
    fake_client = AsyncMock()
    fake_client.post.return_value = _ok_response({"candidates": []})
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(
        "backend.categorizer.gemma_client.httpx.AsyncClient",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        "backend.categorizer.gemma_client.settings.GEMMA_API_KEY", "test-key"
    )

    result = await call_gemma("prompt")
    assert result == ""


@pytest.mark.asyncio
async def test_missing_api_key_returns_empty(monkeypatch):
    """No API key configured returns empty string without making a request."""
    monkeypatch.setattr(
        "backend.categorizer.gemma_client.settings.GEMMA_API_KEY", ""
    )

    result = await call_gemma("prompt")
    assert result == ""


@pytest.mark.asyncio
async def test_server_error_retries_then_returns_empty(monkeypatch):
    """500 errors trigger retries; after max retries, returns empty."""
    fake_client = AsyncMock()
    fake_client.post.return_value = _error_response(500)
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(
        "backend.categorizer.gemma_client.httpx.AsyncClient",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        "backend.categorizer.gemma_client.settings.GEMMA_API_KEY", "test-key"
    )
    monkeypatch.setattr("backend.categorizer.gemma_client.asyncio.sleep", _noop_sleep)

    result = await call_gemma("prompt", max_retries=3)
    assert result == ""
    assert fake_client.post.call_count == 3


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt(monkeypatch):
    """First call fails with timeout, second succeeds."""
    fake_client = AsyncMock()
    fake_client.post.side_effect = [
        httpx.TimeoutException("timed out"),
        _ok_response(_gemma_response('{"ok": true}')),
    ]
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(
        "backend.categorizer.gemma_client.httpx.AsyncClient",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        "backend.categorizer.gemma_client.settings.GEMMA_API_KEY", "test-key"
    )
    monkeypatch.setattr("backend.categorizer.gemma_client.asyncio.sleep", _noop_sleep)

    result = await call_gemma("prompt", max_retries=3)
    assert result == '{"ok": true}'
    assert fake_client.post.call_count == 2


@pytest.mark.asyncio
async def test_client_error_returns_empty_no_retry(monkeypatch):
    """4xx errors (non-server) return empty immediately, no retry."""
    fake_client = AsyncMock()
    fake_client.post.return_value = _error_response(403)
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(
        "backend.categorizer.gemma_client.httpx.AsyncClient",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        "backend.categorizer.gemma_client.settings.GEMMA_API_KEY", "test-key"
    )

    result = await call_gemma("prompt", max_retries=3)
    assert result == ""
    assert fake_client.post.call_count == 1
