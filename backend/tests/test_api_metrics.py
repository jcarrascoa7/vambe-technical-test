from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.routes.metrics import router as metrics_router
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


# ponytail: test app without lifespan — avoids ETL/categorizer startup against real DB
_test_app = FastAPI()
_test_app.include_router(metrics_router)
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


def _seed(db, count=1, **overrides):
    """Insert categorized clients into the test DB."""
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
    for i in range(count):
        db.add(Client(**defaults))
    db.commit()


class TestCloseRateBySector:
    def test_returns_close_rate(self, client, db):
        _seed(db, count=3, sector="Retail", closed=True)
        _seed(db, count=2, sector="Retail", closed=False, email="r2@e.com")
        _seed(db, count=1, sector="Health", closed=True, email="h@e.com")
        resp = client.get("/metrics/close-rate-by-sector")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "close_rate_by_sector"
        sectors = {r["sector"]: r for r in data["data"]}
        assert sectors["Retail"]["total"] == 5
        assert sectors["Retail"]["closed_count"] == 3
        assert sectors["Retail"]["close_rate"] == 0.6
        assert sectors["Health"]["total"] == 1
        assert sectors["Health"]["close_rate"] == 1.0

    def test_excludes_not_specified(self, client, db):
        _seed(db, sector="Retail", closed=True)
        _seed(db, sector="Not specified", closed=True, email="ns@e.com")
        resp = client.get("/metrics/close-rate-by-sector")
        data = resp.json()
        sectors = [r["sector"] for r in data["data"]]
        assert "Not specified" not in sectors
        assert len(data["data"]) == 1


class TestCloseRateByVendorSector:
    def test_returns_heatmap_data(self, client, db):
        _seed(db, vendor="Toro", sector="Retail", closed=True)
        _seed(db, vendor="Toro", sector="Retail", closed=False, email="v2@e.com")
        _seed(db, vendor="Puma", sector="Health", closed=True, email="p@e.com")
        resp = client.get("/metrics/close-rate-by-vendor-sector")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "close_rate_by_vendor_sector"
        assert len(data["data"]) == 2
        combo = {(r["vendor"], r["sector"]): r for r in data["data"]}
        assert combo[("Toro", "Retail")]["close_rate"] == 0.5
        assert combo[("Puma", "Health")]["close_rate"] == 1.0


class TestCloseRateBySource:
    def test_returns_close_rate_per_source(self, client, db):
        _seed(db, source="LinkedIn", closed=True)
        _seed(db, source="LinkedIn", closed=False, email="l2@e.com")
        _seed(db, source="Google", closed=True, email="g@e.com")
        resp = client.get("/metrics/close-rate-by-source")
        assert resp.status_code == 200
        data = resp.json()
        sources = {r["source"]: r for r in data["data"]}
        assert sources["LinkedIn"]["close_rate"] == 0.5
        assert sources["Google"]["close_rate"] == 1.0

    def test_accepts_filter_params(self, client, db):
        _seed(db, source="LinkedIn", sector="Retail", closed=True)
        _seed(db, source="Google", sector="Health", closed=True, email="g@e.com")
        resp = client.get("/metrics/close-rate-by-source", params={"sector": "Retail"})
        assert resp.status_code == 200
        data = resp.json()
        sources = {r["source"]: r for r in data["data"]}
        assert "LinkedIn" in sources
        assert "Google" not in sources


class TestPainDistributionBySector:
    def test_returns_pain_counts(self, client, db):
        _seed(db, sector="Retail", pain="High message volume")
        _seed(db, sector="Retail", pain="High message volume", email="p2@e.com")
        _seed(db, sector="Retail", pain="Slow response", email="p3@e.com")
        _seed(db, sector="Health", pain="Lost leads/follow-up", email="h@e.com")
        resp = client.get("/metrics/pain-distribution-by-sector")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "pain_distribution_by_sector"
        entries = {(r["sector"], r["pain"]): r["count"] for r in data["data"]}
        assert entries[("Retail", "High message volume")] == 2
        assert entries[("Retail", "Slow response")] == 1
        assert entries[("Health", "Lost leads/follow-up")] == 1

    def test_accepts_filter_params(self, client, db):
        _seed(db, sector="Retail", pain="High message volume", vendor="Toro")
        _seed(db, sector="Health", pain="Slow response", vendor="Puma", email="h@e.com")
        resp = client.get("/metrics/pain-distribution-by-sector", params={"vendor": "Toro"})
        assert resp.status_code == 200
        data = resp.json()
        sectors = [r["sector"] for r in data["data"]]
        assert "Retail" in sectors
        assert "Health" not in sectors


class TestCloseRateByConcreteness:
    def test_returns_close_rate(self, client, db):
        _seed(db, concreteness="Concrete", closed=True)
        _seed(db, concreteness="Tentative", closed=False, email="t@e.com")
        _seed(db, concreteness="Tentative", closed=False, email="t2@e.com")
        resp = client.get("/metrics/close-rate-by-concreteness")
        assert resp.status_code == 200
        data = resp.json()
        levels = {r["concreteness"]: r for r in data["data"]}
        assert levels["Concrete"]["close_rate"] == 1.0
        assert levels["Tentative"]["close_rate"] == 0.0

    def test_accepts_filter_params(self, client, db):
        _seed(db, concreteness="Concrete", sector="Retail", closed=True)
        _seed(db, concreteness="Tentative", sector="Health", closed=False, email="t@e.com")
        resp = client.get("/metrics/close-rate-by-concreteness", params={"sector": "Retail"})
        assert resp.status_code == 200
        data = resp.json()
        levels = {r["concreteness"]: r for r in data["data"]}
        assert "Concrete" in levels
        assert "Tentative" not in levels


class TestSectorDistribution:
    def test_returns_distribution(self, client, db):
        _seed(db, count=3, sector="Retail")
        _seed(db, count=1, sector="Health", email="h@e.com")
        resp = client.get("/metrics/sector-distribution")
        assert resp.status_code == 200
        data = resp.json()
        sectors = {r["sector"]: r for r in data["data"]}
        assert sectors["Retail"]["count"] == 3
        assert sectors["Retail"]["percentage"] == 0.75
        assert sectors["Health"]["count"] == 1
        assert sectors["Health"]["percentage"] == 0.25

    def test_accepts_filter_params(self, client, db):
        _seed(db, sector="Retail", vendor="Toro")
        _seed(db, sector="Health", vendor="Puma", email="h@e.com")
        resp = client.get("/metrics/sector-distribution", params={"vendor": "Toro"})
        assert resp.status_code == 200
        data = resp.json()
        sectors = {r["sector"]: r for r in data["data"]}
        assert "Retail" in sectors
        assert "Health" not in sectors


class TestAvgVolumeBySector:
    def test_returns_avg_volume(self, client, db):
        _seed(db, sector="Retail", inquiry_volume="Low")  # 250
        _seed(db, sector="Retail", inquiry_volume="High", email="r2@e.com")  # 3500
        _seed(db, sector="Health", inquiry_volume="Medium", email="h@e.com")  # 1250
        resp = client.get("/metrics/avg-volume-by-sector")
        assert resp.status_code == 200
        data = resp.json()
        sectors = {r["sector"]: r for r in data["data"]}
        assert sectors["Retail"]["avg_volume"] == 1875.0  # (250+3500)/2
        assert sectors["Health"]["avg_volume"] == 1250.0


class TestIntegrationsDistribution:
    def test_returns_integration_counts(self, client, db):
        _seed(db, integrations="CRM, ERP")
        _seed(db, integrations="CRM, POS", email="i2@e.com")
        _seed(db, integrations="CRM", email="i3@e.com")
        resp = client.get("/metrics/integrations-distribution")
        assert resp.status_code == 200
        data = resp.json()
        counts = {r["integration"]: r["count"] for r in data["data"]}
        assert counts["CRM"] == 3
        assert counts["ERP"] == 1
        assert counts["POS"] == 1


class TestCloseRateByChannel:
    def test_returns_close_rate(self, client, db):
        _seed(db, channel="WhatsApp", closed=True)
        _seed(db, channel="WhatsApp", closed=False, email="w2@e.com")
        _seed(db, channel="Email", closed=True, email="e@e.com")
        resp = client.get("/metrics/close-rate-by-channel")
        assert resp.status_code == 200
        data = resp.json()
        channels = {r["channel"]: r for r in data["data"]}
        assert channels["WhatsApp"]["close_rate"] == 0.5
        assert channels["Email"]["close_rate"] == 1.0


class TestTemporalEvolution:
    def test_returns_monthly_data(self, client, db):
        _seed(db, meeting_date=datetime(2024, 1, 15), closed=True)
        _seed(db, meeting_date=datetime(2024, 1, 20), closed=False, email="t2@e.com")
        _seed(db, meeting_date=datetime(2024, 2, 10), closed=True, email="t3@e.com")
        resp = client.get("/metrics/temporal-evolution")
        assert resp.status_code == 200
        data = resp.json()
        months = {r["month"]: r for r in data["data"]}
        assert months["2024-01"]["leads"] == 2
        assert months["2024-01"]["closes"] == 1
        assert months["2024-02"]["leads"] == 1
        assert months["2024-02"]["closes"] == 1


class TestTopSectorsByVolumeRate:
    def test_returns_ranked_sectors(self, client, db):
        # Retail: avg_vol=3500, close_rate=1.0, score=3500
        _seed(db, sector="Retail", inquiry_volume="High", closed=True)
        # Health: avg_vol=250, close_rate=0.0, score=0
        _seed(db, sector="Health", inquiry_volume="Low", closed=False, email="h@e.com")
        resp = client.get("/metrics/top-sectors-by-volume-rate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "top_sectors_by_volume_rate"
        assert data["data"][0]["sector"] == "Retail"
        assert data["data"][0]["volume_rate_score"] == 3500.0


class TestMetricsStatus:
    def test_returns_status(self, client, db):
        _seed(db, count=3, categorized=True)
        _seed(db, count=2, categorized=False, email="uncat@e.com")
        resp = client.get("/metrics/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert data["categorized"] == 3
        assert data["progress"] == 60.0
        assert data["is_complete"] is False

    def test_complete_status(self, client, db):
        _seed(db, count=5, categorized=True)
        resp = client.get("/metrics/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert data["categorized"] == 5
        assert data["progress"] == 100.0
        assert data["is_complete"] is True


class TestZeroRecordsEdgeCase:
    """All metric endpoints must return empty data / zero status on empty DB."""

    def test_close_rate_by_sector_empty(self, client):
        resp = client.get("/metrics/close-rate-by-sector")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_close_rate_by_vendor_sector_empty(self, client):
        resp = client.get("/metrics/close-rate-by-vendor-sector")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_close_rate_by_source_empty(self, client):
        resp = client.get("/metrics/close-rate-by-source")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_pain_distribution_empty(self, client):
        resp = client.get("/metrics/pain-distribution-by-sector")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_close_rate_by_concreteness_empty(self, client):
        resp = client.get("/metrics/close-rate-by-concreteness")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_sector_distribution_empty(self, client):
        resp = client.get("/metrics/sector-distribution")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_avg_volume_empty(self, client):
        resp = client.get("/metrics/avg-volume-by-sector")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_integrations_empty(self, client):
        resp = client.get("/metrics/integrations-distribution")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_close_rate_by_channel_empty(self, client):
        resp = client.get("/metrics/close-rate-by-channel")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_temporal_evolution_empty(self, client):
        resp = client.get("/metrics/temporal-evolution")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_top_sectors_empty(self, client):
        resp = client.get("/metrics/top-sectors-by-volume-rate")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_status_empty(self, client):
        resp = client.get("/metrics/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["categorized"] == 0
        assert data["progress"] == 0.0
        assert data["is_complete"] is False
