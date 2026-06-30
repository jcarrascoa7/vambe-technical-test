"""Tests for the LLM-generated chart insights endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.insights import router as insights_router

_test_app = FastAPI()
_test_app.include_router(insights_router)


@pytest.fixture
def client():
    with TestClient(_test_app) as c:
        yield c


class TestInsightSuccess:
    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_returns_llm_decision(self, mock_llm, client):
        mock_llm.return_value = (
            '{"decision": "Priorizar sectores con mayor tasa de cierre."}'
        )
        resp = client.get("/insights/close-rate-by-sector")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart_type"] == "close-rate-by-sector"
        assert "sectores" in data["decision"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_handles_plain_text_response(self, mock_llm, client):
        mock_llm.return_value = "Priorizar sectores con mayor tasa de cierre."
        resp = client.get("/insights/sector-distribution")
        assert resp.status_code == 200
        assert "sectores" in resp.json()["decision"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_all_chart_types_accepted(self, mock_llm, client):
        mock_llm.return_value = '{"decision": "Análisis del gráfico."}'
        for chart_type in [
            "close-rate-by-sector",
            "sector-distribution",
            "pain-distribution",
            "close-rate-by-source",
            "close-rate-by-concreteness",
            "vendor-sector-heatmap",
            "temporal-evolution",
            "integrations-distribution",
            "volume-close-rate",
        ]:
            resp = client.get(f"/insights/{chart_type}")
            assert resp.status_code == 200
            assert resp.json()["chart_type"] == chart_type

    def test_justification_within_word_limit(self, client):
        resp = client.get("/insights/close-rate-by-sector")
        assert resp.status_code == 200
        justification = resp.json()["justification"]
        assert len(justification.split()) <= 25


class TestInsightFallback:
    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_fallback_on_empty_llm_response(self, mock_llm, client):
        mock_llm.return_value = ""
        resp = client.get("/insights/close-rate-by-sector")
        assert resp.status_code == 200
        assert "No se pudo generar" in resp.json()["decision"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_fallback_on_malformed_json(self, mock_llm, client):
        mock_llm.return_value = "not json {"
        resp = client.get("/insights/sector-distribution")
        assert resp.status_code == 200
        assert resp.json()["decision"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_fallback_on_empty_json_decision_field(self, mock_llm, client):
        mock_llm.return_value = '{"decision": ""}'
        resp = client.get("/insights/close-rate-by-source")
        assert resp.status_code == 200
        assert "No se pudo generar" in resp.json()["decision"]

    def test_unknown_chart_type(self, client):
        resp = client.get("/insights/unknown-chart")
        assert resp.status_code == 200
        assert "no reconocido" in resp.json()["decision"]


class TestInsightSkeletonState:
    """The skeleton/loading state is handled entirely on the frontend.
    The backend always returns a response (either LLM decision or fallback).
    These tests verify the response structure is consistent."""

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_response_has_required_fields(self, mock_llm, client):
        mock_llm.return_value = '{"decision": "Análisis."}'
        resp = client.get("/insights/close-rate-by-sector")
        data = resp.json()
        assert "chart_type" in data
        assert "justification" in data
        assert "decision" in data
        assert isinstance(data["decision"], str)

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_response_structure_on_failure(self, mock_llm, client):
        mock_llm.return_value = ""
        resp = client.get("/insights/close-rate-by-sector")
        data = resp.json()
        assert "chart_type" in data
        assert "justification" in data
        assert "decision" in data
        assert len(data["decision"]) > 0
