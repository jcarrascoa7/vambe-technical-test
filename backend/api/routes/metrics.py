from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.api.schemas import MetricResponse, StatusResponse
from backend.database import get_db
from backend.models import Client

router = APIRouter(prefix="/metrics", tags=["metrics"])

NOT_SPECIFIED = "Not specified"


def _categorized_only(db: Session):
    """Base query: only categorized records."""
    return db.query(Client).filter(Client.categorized == True)  # noqa: E712


def _apply_filters(query, sector, size, volume, source, channel, vendor, closed, date_from, date_to):
    """Apply optional filters to a query."""
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
    return query


@router.get("/close-rate-by-sector", response_model=MetricResponse)
def close_rate_by_sector(
    sector: Optional[str] = None,
    size: Optional[str] = None,
    volume: Optional[str] = None,
    source: Optional[str] = None,
    channel: Optional[str] = None,
    vendor: Optional[str] = None,
    closed: Optional[bool] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Close rate per sector (closed=1 by sector / total by sector)."""
    query = _categorized_only(db)
    query = _apply_filters(query, sector, size, volume, source, channel, vendor, closed, date_from, date_to)
    rows = (
        query
        .filter(Client.sector != NOT_SPECIFIED, Client.sector.isnot(None))
        .with_entities(
            Client.sector,
            func.count().label("total"),
            func.sum(case((Client.closed == True, 1), else_=0)).label("closed_count"),  # noqa: E712
        )
        .group_by(Client.sector)
        .all()
    )
    data = [
        {
            "sector": r.sector,
            "total": r.total,
            "closed_count": int(r.closed_count or 0),
            "close_rate": round(int(r.closed_count or 0) / r.total, 4) if r.total else 0,
        }
        for r in rows
    ]
    return MetricResponse(metric="close_rate_by_sector", data=data)


@router.get("/close-rate-by-vendor-sector", response_model=MetricResponse)
def close_rate_by_vendor_sector(
    sector: Optional[str] = None,
    size: Optional[str] = None,
    volume: Optional[str] = None,
    source: Optional[str] = None,
    channel: Optional[str] = None,
    vendor: Optional[str] = None,
    closed: Optional[bool] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Heatmap-ready data: close rate by (vendor, sector)."""
    query = _categorized_only(db)
    query = _apply_filters(query, sector, size, volume, source, channel, vendor, closed, date_from, date_to)
    rows = (
        query
        .filter(Client.sector != NOT_SPECIFIED, Client.sector.isnot(None))
        .with_entities(
            Client.vendor,
            Client.sector,
            func.count().label("total"),
            func.sum(case((Client.closed == True, 1), else_=0)).label("closed_count"),  # noqa: E712
        )
        .group_by(Client.vendor, Client.sector)
        .all()
    )
    data = [
        {
            "vendor": r.vendor,
            "sector": r.sector,
            "total": r.total,
            "closed_count": int(r.closed_count or 0),
            "close_rate": round(int(r.closed_count or 0) / r.total, 4) if r.total else 0,
        }
        for r in rows
    ]
    return MetricResponse(metric="close_rate_by_vendor_sector", data=data)


@router.get("/close-rate-by-source", response_model=MetricResponse)
def close_rate_by_source(db: Session = Depends(get_db)):
    """Close rate per acquisition source."""
    rows = (
        _categorized_only(db)
        .filter(Client.source != NOT_SPECIFIED, Client.source.isnot(None))
        .with_entities(
            Client.source,
            func.count().label("total"),
            func.sum(case((Client.closed == True, 1), else_=0)).label("closed_count"),  # noqa: E712
        )
        .group_by(Client.source)
        .all()
    )
    data = [
        {
            "source": r.source,
            "total": r.total,
            "closed_count": int(r.closed_count or 0),
            "close_rate": round(int(r.closed_count or 0) / r.total, 4) if r.total else 0,
        }
        for r in rows
    ]
    return MetricResponse(metric="close_rate_by_source", data=data)


@router.get("/pain-distribution-by-sector", response_model=MetricResponse)
def pain_distribution_by_sector(db: Session = Depends(get_db)):
    """Count of each pain category per sector."""
    rows = (
        _categorized_only(db)
        .filter(
            Client.pain != NOT_SPECIFIED,
            Client.pain.isnot(None),
            Client.sector != NOT_SPECIFIED,
            Client.sector.isnot(None),
        )
        .with_entities(
            Client.sector,
            Client.pain,
            func.count().label("count"),
        )
        .group_by(Client.sector, Client.pain)
        .all()
    )
    data = [
        {"sector": r.sector, "pain": r.pain, "count": r.count}
        for r in rows
    ]
    return MetricResponse(metric="pain_distribution_by_sector", data=data)


@router.get("/close-rate-by-concreteness", response_model=MetricResponse)
def close_rate_by_concreteness(db: Session = Depends(get_db)):
    """Close rate per language concreteness level."""
    rows = (
        _categorized_only(db)
        .filter(Client.concreteness != NOT_SPECIFIED, Client.concreteness.isnot(None))
        .with_entities(
            Client.concreteness,
            func.count().label("total"),
            func.sum(case((Client.closed == True, 1), else_=0)).label("closed_count"),  # noqa: E712
        )
        .group_by(Client.concreteness)
        .all()
    )
    data = [
        {
            "concreteness": r.concreteness,
            "total": r.total,
            "closed_count": int(r.closed_count or 0),
            "close_rate": round(int(r.closed_count or 0) / r.total, 4) if r.total else 0,
        }
        for r in rows
    ]
    return MetricResponse(metric="close_rate_by_concreteness", data=data)


@router.get("/sector-distribution", response_model=MetricResponse)
def sector_distribution(db: Session = Depends(get_db)):
    """Count by sector / total."""
    rows = (
        _categorized_only(db)
        .filter(Client.sector != NOT_SPECIFIED, Client.sector.isnot(None))
        .with_entities(
            Client.sector,
            func.count().label("count"),
        )
        .group_by(Client.sector)
        .all()
    )
    total = sum(r.count for r in rows)
    data = [
        {
            "sector": r.sector,
            "count": r.count,
            "percentage": round(r.count / total, 4) if total else 0,
        }
        for r in rows
    ]
    return MetricResponse(metric="sector_distribution", data=data)


# ponytail: map inquiry_volume strings to numeric midpoints for averaging
_VOLUME_MAP = {"Low": 250, "Medium": 1250, "High": 3500, "Very High": 7500}


@router.get("/avg-volume-by-sector", response_model=MetricResponse)
def avg_volume_by_sector(db: Session = Depends(get_db)):
    """Average monthly inquiry volume grouped by sector."""
    rows = (
        _categorized_only(db)
        .filter(
            Client.inquiry_volume != NOT_SPECIFIED,
            Client.inquiry_volume.isnot(None),
            Client.sector != NOT_SPECIFIED,
            Client.sector.isnot(None),
        )
        .with_entities(
            Client.sector,
            Client.inquiry_volume,
            func.count().label("count"),
        )
        .group_by(Client.sector, Client.inquiry_volume)
        .all()
    )
    # Aggregate per sector: sum(count * volume_value) / sum(count)
    sector_totals: dict[str, float] = {}
    sector_counts: dict[str, int] = {}
    for r in rows:
        vol = _VOLUME_MAP.get(r.inquiry_volume, 0)
        sector_totals[r.sector] = sector_totals.get(r.sector, 0) + vol * r.count
        sector_counts[r.sector] = sector_counts.get(r.sector, 0) + r.count
    data = [
        {
            "sector": s,
            "avg_volume": round(sector_totals[s] / sector_counts[s], 2) if sector_counts[s] else 0,
            "total_records": sector_counts[s],
        }
        for s in sorted(sector_totals)
    ]
    return MetricResponse(metric="avg_volume_by_sector", data=data)


@router.get("/integrations-distribution", response_model=MetricResponse)
def integrations_distribution(db: Session = Depends(get_db)):
    """Count of each integration type."""
    rows = (
        _categorized_only(db)
        .filter(Client.integrations != NOT_SPECIFIED, Client.integrations.isnot(None))
        .with_entities(Client.integrations)
        .all()
    )
    counts: dict[str, int] = {}
    for (integrations,) in rows:
        for item in integrations.split(","):
            item = item.strip()
            if item:
                counts[item] = counts.get(item, 0) + 1
    data = [{"integration": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]
    return MetricResponse(metric="integrations_distribution", data=data)


@router.get("/close-rate-by-channel", response_model=MetricResponse)
def close_rate_by_channel(db: Session = Depends(get_db)):
    """Close rate per main contact channel."""
    rows = (
        _categorized_only(db)
        .filter(Client.channel != NOT_SPECIFIED, Client.channel.isnot(None))
        .with_entities(
            Client.channel,
            func.count().label("total"),
            func.sum(case((Client.closed == True, 1), else_=0)).label("closed_count"),  # noqa: E712
        )
        .group_by(Client.channel)
        .all()
    )
    data = [
        {
            "channel": r.channel,
            "total": r.total,
            "closed_count": int(r.closed_count or 0),
            "close_rate": round(int(r.closed_count or 0) / r.total, 4) if r.total else 0,
        }
        for r in rows
    ]
    return MetricResponse(metric="close_rate_by_channel", data=data)


@router.get("/temporal-evolution", response_model=MetricResponse)
def temporal_evolution(db: Session = Depends(get_db)):
    """Leads and closes grouped by month."""
    # ponytail: group in Python to avoid DB-specific date functions (to_char vs strftime)
    rows = (
        _categorized_only(db)
        .filter(Client.meeting_date.isnot(None))
        .with_entities(Client.meeting_date, Client.closed)
        .all()
    )
    months: dict[str, dict] = {}
    for dt, closed in rows:
        key = f"{dt.year:04d}-{dt.month:02d}"
        if key not in months:
            months[key] = {"leads": 0, "closes": 0}
        months[key]["leads"] += 1
        if closed:
            months[key]["closes"] += 1
    data = [
        {
            "month": k,
            "leads": v["leads"],
            "closes": v["closes"],
            "close_rate": round(v["closes"] / v["leads"], 4) if v["leads"] else 0,
        }
        for k, v in sorted(months.items())
    ]
    return MetricResponse(metric="temporal_evolution", data=data)


@router.get("/top-sectors-by-volume-rate", response_model=MetricResponse)
def top_sectors_by_volume_rate(db: Session = Depends(get_db)):
    """Sectors ranked by avg_volume * close_rate."""
    # Get close rate per sector
    close_rows = (
        _categorized_only(db)
        .filter(Client.sector != NOT_SPECIFIED, Client.sector.isnot(None))
        .with_entities(
            Client.sector,
            func.count().label("total"),
            func.sum(case((Client.closed == True, 1), else_=0)).label("closed_count"),  # noqa: E712
        )
        .group_by(Client.sector)
        .all()
    )
    close_map = {r.sector: (int(r.closed_count or 0) / r.total if r.total else 0) for r in close_rows}

    # Get avg volume per sector
    vol_rows = (
        _categorized_only(db)
        .filter(
            Client.inquiry_volume != NOT_SPECIFIED,
            Client.inquiry_volume.isnot(None),
            Client.sector != NOT_SPECIFIED,
            Client.sector.isnot(None),
        )
        .with_entities(
            Client.sector,
            Client.inquiry_volume,
            func.count().label("count"),
        )
        .group_by(Client.sector, Client.inquiry_volume)
        .all()
    )
    sector_totals: dict[str, float] = {}
    sector_counts: dict[str, int] = {}
    for r in vol_rows:
        vol = _VOLUME_MAP.get(r.inquiry_volume, 0)
        sector_totals[r.sector] = sector_totals.get(r.sector, 0) + vol * r.count
        sector_counts[r.sector] = sector_counts.get(r.sector, 0) + r.count

    data = []
    for sector in close_map:
        avg_vol = sector_totals.get(sector, 0) / sector_counts.get(sector, 1) if sector_counts.get(sector) else 0
        rate = close_map.get(sector, 0)
        data.append({
            "sector": sector,
            "avg_volume": round(avg_vol, 2),
            "close_rate": round(rate, 4),
            "volume_rate_score": round(avg_vol * rate, 2),
        })
    data.sort(key=lambda x: -x["volume_rate_score"])
    return MetricResponse(metric="top_sectors_by_volume_rate", data=data)


@router.get("/status", response_model=StatusResponse)
def metrics_status(db: Session = Depends(get_db)):
    """Total, categorized count, progress percentage, is_complete boolean."""
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
