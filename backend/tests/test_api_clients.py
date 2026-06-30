from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.routes.clients import router as clients_router
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
_test_app.include_router(clients_router)
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


class TestListClientsNoFilters:
    def test_returns_paginated_results(self, client, db):
        _seed(db, count=100)
        resp = client.get("/clients?limit=5&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 5
        assert data["total"] == 100
        assert data["limit"] == 5
        assert data["offset"] == 0

    def test_default_pagination(self, client, db):
        _seed(db, count=3)
        resp = client.get("/clients")
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["items"]) == 3

    def test_only_returns_categorized(self, client, db):
        _seed(db, count=3, categorized=True)
        _seed(db, count=2, categorized=False, email="uncat@example.com")
        resp = client.get("/clients")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3


class TestListClientsSingleFilter:
    def test_filter_by_sector(self, client, db):
        _seed(db, sector="Retail")
        _seed(db, sector="Health", email="h@e.com")
        resp = client.get("/clients?sector=Health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["sector"] == "Health"

    def test_filter_by_vendor(self, client, db):
        _seed(db, vendor="Toro")
        _seed(db, vendor="Puma", email="p@e.com")
        resp = client.get("/clients?vendor=Puma")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_size(self, client, db):
        _seed(db, size="Small")
        _seed(db, size="Large", email="l@e.com")
        resp = client.get("/clients?size=Large")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_volume(self, client, db):
        _seed(db, inquiry_volume="Low")
        _seed(db, inquiry_volume="High", email="h@e.com")
        resp = client.get("/clients?volume=High")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_source(self, client, db):
        _seed(db, source="LinkedIn")
        _seed(db, source="Google", email="g@e.com")
        resp = client.get("/clients?source=Google")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_channel(self, client, db):
        _seed(db, channel="WhatsApp")
        _seed(db, channel="Email", email="e@e.com")
        resp = client.get("/clients?channel=Email")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_closed(self, client, db):
        _seed(db, closed=True)
        _seed(db, closed=False, email="f@e.com")
        resp = client.get("/clients?closed=true")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_date_range(self, client, db):
        _seed(db, meeting_date=datetime(2024, 1, 15))
        _seed(db, meeting_date=datetime(2024, 6, 15), email="j@e.com")
        resp = client.get("/clients?date_from=2024-03-01&date_to=2024-12-31")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestListClientsCombinedFilters:
    def test_sector_and_vendor(self, client, db):
        _seed(db, sector="Retail", vendor="Toro")
        _seed(db, sector="Health", vendor="Toro", email="h@e.com")
        _seed(db, sector="Retail", vendor="Puma", email="p@e.com")
        resp = client.get("/clients?sector=Retail&vendor=Toro")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_all_filters_combined(self, client, db):
        _seed(db)
        resp = client.get(
            "/clients?sector=Retail&size=Small&volume=Medium"
            "&source=LinkedIn&channel=WhatsApp&vendor=Toro"
            "&closed=false&date_from=2024-01-01&date_to=2024-12-31"
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestListClientsSearch:
    def test_search_by_name(self, client, db):
        _seed(db, name="Carlos Lopez")
        _seed(db, name="Maria Perez", email="m@e.com")
        resp = client.get("/clients?search=Carlos")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_by_email(self, client, db):
        _seed(db, email="carlos@example.com")
        _seed(db, email="maria@example.com", name="Maria")
        resp = client.get("/clients?search=carlos@")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_case_insensitive(self, client, db):
        _seed(db, name="CARLOS")
        resp = client.get("/clients?search=carlos")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestListClientsEmptyResults:
    def test_no_matching_clients(self, client, db):
        _seed(db, sector="Retail")
        resp = client.get("/clients?sector=Nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestListClientsPagination:
    def test_offset_and_limit(self, client, db):
        _seed(db, count=100)
        resp = client.get("/clients?limit=10&offset=50")
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 10
        assert data["offset"] == 50
        assert len(data["items"]) == 10


class TestClientStatus:
    def test_returns_status(self, client, db):
        _seed(db, count=50, categorized=True)
        _seed(db, count=50, categorized=False, email="uncat@example.com")
        resp = client.get("/clients/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 100
        assert data["categorized"] == 50
        assert data["progress"] == 50.0
        assert data["is_complete"] is False

    def test_complete_status(self, client, db):
        _seed(db, count=10, categorized=True)
        resp = client.get("/clients/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 10
        assert data["categorized"] == 10
        assert data["progress"] == 100.0
        assert data["is_complete"] is True

    def test_empty_table(self, client):
        resp = client.get("/clients/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["progress"] == 0.0
        assert data["is_complete"] is False
