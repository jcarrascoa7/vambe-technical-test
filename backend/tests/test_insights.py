"""Tests for the LLM-generated chart insights endpoint."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.insights import router as insights_router, _clean_decision
from backend.database import Base, get_db
from backend.models import Client

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


_test_app = FastAPI()
_test_app.include_router(insights_router)
_test_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(_test_app) as c:
        yield c


def _seed(db, **overrides):
    defaults = dict(
        name="Test User",
        email="test@example.com",
        phone="123456",
        meeting_date=datetime(2024, 3, 15),
        vendor="Toro",
        closed=False,
        transcription="text",
        sector="Retail",
        size="Small",
        inquiry_volume="Medium",
        channel="WhatsApp",
        source="LinkedIn",
        integrations="CRM",
        tone="Professional",
        usage_type="FAQ",
        pain="High message volume",
        concreteness="Concrete",
        categorized=True,
    )
    defaults.update(overrides)
    db.add(Client(**defaults))
    db.commit()


class TestCleanDecision:
    def test_strips_json_wrapper(self):
        raw = '{"decision": "Priorizar Retail y Health."}'
        assert _clean_decision(raw) == "Priorizar Retail y Health."

    def test_returns_plain_text_unchanged(self):
        assert _clean_decision("Texto limpio.") == "Texto limpio."

    def test_handles_malformed_json(self):
        assert _clean_decision("not json {") == "not json {"


class TestInsightSuccess:
    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_returns_llm_decision(self, mock_llm, client, db):
        _seed(db, sector="Retail", closed=True)
        _seed(db, sector="Health", closed=False, email="h@e.com")
        mock_llm.return_value = (
            '{"decision": "Priorizar Retail donde la tasa de cierre es más alta."}'
        )
        resp = client.get("/insights/close-rate-by-sector")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart_type"] == "close-rate-by-sector"
        assert "Retail" in data["decision"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_handles_plain_text_response(self, mock_llm, client, db):
        _seed(db, sector="Retail")
        mock_llm.return_value = "Priorizar Retail."
        resp = client.get("/insights/sector-distribution")
        assert resp.status_code == 200
        assert "Retail" in resp.json()["decision"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_all_chart_types_accepted(self, mock_llm, client, db):
        _seed(db)
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

    def test_justification_within_word_limit(self, client, db):
        _seed(db)
        resp = client.get("/insights/close-rate-by-sector")
        assert resp.status_code == 200
        justification = resp.json()["justification"]
        assert len(justification.split()) <= 25

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_prompt_includes_actual_data(self, mock_llm, client, db):
        _seed(db, sector="Retail", closed=True)
        _seed(db, sector="Health", closed=False, email="h@e.com")
        mock_llm.return_value = '{"decision": "Priorizar Retail."}'
        client.get("/insights/close-rate-by-sector")
        prompt = mock_llm.call_args[0][0]
        assert "Retail" in prompt
        assert "Health" in prompt

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_strips_json_wrapper_from_llm_decision(self, mock_llm, client, db):
        _seed(db)
        mock_llm.return_value = '{"decision": "{"decision": "Priorizar Retail."}"}'
        resp = client.get("/insights/close-rate-by-sector")
        assert resp.status_code == 200
        assert resp.json()["decision"] == "Priorizar Retail."


class TestInsightFallback:
    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_fallback_on_empty_llm_response(self, mock_llm, client, db):
        _seed(db)
        mock_llm.return_value = ""
        resp = client.get("/insights/close-rate-by-sector")
        assert resp.status_code == 200
        assert "No se pudo generar" in resp.json()["decision"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_fallback_on_malformed_json(self, mock_llm, client, db):
        _seed(db)
        mock_llm.return_value = "not json {"
        resp = client.get("/insights/sector-distribution")
        assert resp.status_code == 200
        assert resp.json()["decision"]

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_fallback_on_empty_json_decision_field(self, mock_llm, client, db):
        _seed(db)
        mock_llm.return_value = '{"decision": ""}'
        resp = client.get("/insights/close-rate-by-source")
        assert resp.status_code == 200
        assert "No se pudo generar" in resp.json()["decision"]

    def test_unknown_chart_type(self, client, db):
        _seed(db)
        resp = client.get("/insights/unknown-chart")
        assert resp.status_code == 200
        assert "no reconocido" in resp.json()["decision"]


class TestInsightSkeletonState:
    """The skeleton/loading state is handled entirely on the frontend.
    The backend always returns a response (either LLM decision or fallback).
    These tests verify the response structure is consistent."""

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_response_has_required_fields(self, mock_llm, client, db):
        _seed(db)
        mock_llm.return_value = '{"decision": "Análisis."}'
        resp = client.get("/insights/close-rate-by-sector")
        data = resp.json()
        assert "chart_type" in data
        assert "justification" in data
        assert "decision" in data
        assert isinstance(data["decision"], str)

    @patch("backend.api.insights.call_llm", new_callable=AsyncMock)
    def test_response_structure_on_failure(self, mock_llm, client, db):
        _seed(db)
        mock_llm.return_value = ""
        resp = client.get("/insights/close-rate-by-sector")
        data = resp.json()
        assert "chart_type" in data
        assert "justification" in data
        assert "decision" in data
        assert len(data["decision"]) > 0
