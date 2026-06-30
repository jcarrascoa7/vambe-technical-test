from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.api.schemas import (
    ClientListResponse,
    ClientResponse,
    MetricResponse,
    StatusResponse,
)


class TestClientResponse:
    def test_valid_data_serialization(self):
        data = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "phone": "123456",
            "meeting_date": datetime(2024, 3, 15),
            "vendor": "Toro",
            "closed": True,
            "categorized": True,
        }
        client = ClientResponse(**data)
        assert client.id == 1
        assert client.name == "Test User"
        assert client.email == "test@example.com"
        assert client.closed is True
        assert client.categorized is True

    def test_optional_fields_default_none(self):
        data = {"id": 1, "name": "Test User"}
        client = ClientResponse(**data)
        assert client.email is None
        assert client.phone is None
        assert client.meeting_date is None
        assert client.vendor is None
        assert client.sector is None

    def test_bool_fields_default_false(self):
        data = {"id": 1, "name": "Test User"}
        client = ClientResponse(**data)
        assert client.closed is False
        assert client.categorized is False

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            ClientResponse(email="test@example.com")

    def test_type_coercion_from_string(self):
        data = {"id": "1", "name": "Test User", "closed": "true"}
        client = ClientResponse(**data)
        assert client.id == 1
        assert client.closed is True


class TestClientListResponse:
    def test_valid_structure(self):
        data = {
            "items": [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}],
            "total": 10,
            "limit": 50,
            "offset": 0,
        }
        resp = ClientListResponse(**data)
        assert len(resp.items) == 2
        assert resp.total == 10

    def test_empty_items(self):
        data = {"items": [], "total": 0, "limit": 50, "offset": 0}
        resp = ClientListResponse(**data)
        assert len(resp.items) == 0


class TestStatusResponse:
    def test_valid_structure(self):
        data = {"total": 100, "categorized": 50, "progress": 50.0, "is_complete": False}
        resp = StatusResponse(**data)
        assert resp.progress == 50.0
        assert resp.is_complete is False

    def test_progress_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            StatusResponse(total=100, categorized=50, progress=101.0, is_complete=False)


class TestMetricResponse:
    def test_generic_structure(self):
        resp = MetricResponse[str](metric="test", data="value")
        assert resp.metric == "test"
        assert resp.data == "value"

    def test_list_data(self):
        resp = MetricResponse[list](metric="test", data=[1, 2, 3])
        assert len(resp.data) == 3
