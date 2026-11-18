"""
Mandi Price Data Service
Primary Maintainer: Swyam Shukla (Database Lead)

Database query and persistence operations for historical agricultural
wholesale market records.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas


def get_latest_mandi_prices(
    db: Session,
    commodity: Optional[str] = None,
    limit: int = 50,
) -> List[models.MandiPriceRecord]:
    """Retrieve historical mandi price records, optionally filtered by commodity."""
    query = db.query(models.MandiPriceRecord)
    if commodity:
        query = query.filter(models.MandiPriceRecord.commodity.ilike(f"%{commodity.strip()}%"))
    return query.order_by(models.MandiPriceRecord.arrival_date.desc()).limit(limit).all()


def get_commodity_summary(
    db: Session,
    commodity: str,
) -> Optional[Dict[str, Any]]:
    """Compute aggregate price statistics for a specific commodity from stored records."""
    records = (
        db.query(models.MandiPriceRecord)
        .filter(models.MandiPriceRecord.commodity.ilike(f"%{commodity.strip()}%"))
        .order_by(models.MandiPriceRecord.arrival_date.desc())
        .limit(14)
        .all()
    )
    if not records:
        return None

    modal_prices = [r.modal_price for r in records]
    avg_modal = sum(modal_prices) / len(modal_prices)
    latest_record = records[0]

    return {
        "commodity": latest_record.commodity,
        "market": latest_record.market,
        "state": latest_record.state,
        "latest_arrival_date": latest_record.arrival_date,
        "latest_modal_quintal": latest_record.modal_price,
        "latest_modal_kg": round(latest_record.modal_price / 100.0, 2),
        "moving_average_kg": round(avg_modal / 100.0, 2),
        "min_price_quintal": min(r.min_price for r in records),
        "max_price_quintal": max(r.max_price for r in records),
        "sample_days": len(records),
    }


def add_mandi_price_record(
    db: Session,
    payload: schemas.MandiPriceCreate,
) -> models.MandiPriceRecord:
    """Insert a new validated mandi price record into persistence."""
    record = models.MandiPriceRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
