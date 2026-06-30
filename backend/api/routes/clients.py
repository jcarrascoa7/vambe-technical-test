from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.api.schemas import ClientListResponse, ClientResponse, StatusResponse
from backend.database import get_db
from backend.models import Client

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=ClientListResponse)
def list_clients(
    sector: Optional[str] = None,
    size: Optional[str] = None,
    volume: Optional[str] = None,
    source: Optional[str] = None,
    channel: Optional[str] = None,
    vendor: Optional[str] = None,
    closed: Optional[bool] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ClientListResponse:
    """List clients with optional filters, search, and pagination."""
    query = db.query(Client).filter(Client.categorized == True)  # noqa: E712

    if sector is not None:
        query = query.filter(Client.sector == sector)
    if size is not None:
        query = query.filter(Client.size == size)
    if volume is not None:
        query = query.filter(Client.inquiry_volume == volume)
    if source is not None:
        query = query.filter(Client.source == source)
    if channel is not None:
        query = query.filter(Client.channel == channel)
    if vendor is not None:
        query = query.filter(Client.vendor == vendor)
    if closed is not None:
        query = query.filter(Client.closed == closed)
    if date_from is not None:
        query = query.filter(Client.meeting_date >= date_from)
    if date_to is not None:
        query = query.filter(Client.meeting_date <= date_to)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(Client.name.ilike(pattern), Client.email.ilike(pattern))
        )

    total = query.count()
    items = query.order_by(Client.id).offset(offset).limit(limit).all()

    return ClientListResponse(
        items=[ClientResponse.model_validate(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/status", response_model=StatusResponse)
def client_status(db: Session = Depends(get_db)) -> StatusResponse:
    """Categorization progress status."""
    total = db.query(func.count(Client.id)).scalar()
    categorized = (
        db.query(func.count(Client.id))
        .filter(Client.categorized == True)  # noqa: E712
        .scalar()
    )
    progress = (categorized / total * 100) if total > 0 else 0.0

    return StatusResponse(
        total=total,
        categorized=categorized,
        progress=round(progress, 2),
        is_complete=categorized == total and total > 0,
    )
