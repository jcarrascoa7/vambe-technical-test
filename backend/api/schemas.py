from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ClientResponse(BaseModel):
    """Single client serialized for API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    meeting_date: Optional[datetime] = None
    vendor: Optional[str] = None
    closed: bool = False
    transcription: Optional[str] = None
    sector: Optional[str] = None
    size: Optional[str] = None
    inquiry_volume: Optional[str] = None
    channel: Optional[str] = None
    source: Optional[str] = None
    integrations: Optional[str] = None
    tone: Optional[str] = None
    usage_type: Optional[str] = None
    pain: Optional[str] = None
    concreteness: Optional[str] = None
    categorized: bool = False


class ClientListResponse(BaseModel):
    """Paginated list of clients."""

    items: list[ClientResponse]
    total: int
    limit: int
    offset: int


class StatusResponse(BaseModel):
    """Categorization progress status."""

    total: int
    categorized: int
    progress: float = Field(ge=0, le=100)
    is_complete: bool


class MetricResponse(BaseModel, Generic[T]):
    """Generic structure for metric data."""

    metric: str
    data: T
