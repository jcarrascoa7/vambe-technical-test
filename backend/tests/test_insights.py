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
    def test_returns_llm_text(self, mock_llm, client):
        mock_llm.return_value = '{"text": "Este gráfico muestra la tasa de cierre por sector."}'
        resp = client.get("/insights/close-rate-by-sector")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart_type"] == "close-rate-by-sector"
        assert "tasa de cierre" in data["text"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_handles_plain_text_response(self, mock_llm, client):
        mock_llm.return_value = "Este gráfico muestra la distribución de sectores."
        resp = client.get("/insights/sector-distribution")
        assert resp.status_code == 200
        assert "distribución" in resp.json()["text"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_all_chart_types_accepted(self, mock_llm, client):
        mock_llm.return_value = '{"text": "Análisis del gráfico."}'
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


class TestInsightFallback:
    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_fallback_on_empty_llm_response(self, mock_llm, client):
        mock_llm.return_value = ""
        resp = client.get("/insights/close-rate-by-sector")
        assert resp.status_code == 200
        assert "No se pudo generar" in resp.json()["text"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_fallback_on_malformed_json(self, mock_llm, client):
        mock_llm.return_value = "not json {"
        resp = client.get("/insights/sector-distribution")
        assert resp.status_code == 200
        assert resp.json()["text"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_fallback_on_empty_json_text_field(self, mock_llm, client):
        mock_llm.return_value = '{"text": ""}'
        resp = client.get("/insights/close-rate-by-source")
        assert resp.status_code == 200
        assert "No se pudo generar" in resp.json()["text"]

    def test_unknown_chart_type(self, client):
        resp = client.get("/insights/unknown-chart")
        assert resp.status_code == 200
        assert "no reconocido" in resp.json()["text"]


class TestInsightSkeletonState:
    """The skeleton/loading state is handled entirely on the frontend.
    The backend always returns a response (either LLM text or fallback).
    These tests verify the response structure is consistent."""

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_response_has_required_fields(self, mock_llm, client):
        mock_llm.return_value = '{"text": "Análisis."}'
        resp = client.get("/insights/close-rate-by-sector")
        data = resp.json()
        assert "chart_type" in data
        assert "text" in data
        assert isinstance(data["text"], str)

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_response_structure_on_failure(self, mock_llm, client):
        mock_llm.return_value = ""
        resp = client.get("/insights/close-rate-by-sector")
        data = resp.json()
        assert "chart_type" in data
        assert "text" in data
        assert len(data["text"]) > 0
