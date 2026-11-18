"""
Analytics & Market Intelligence Router
Primary Maintainer: Swyam Shukla (Database Lead & API Integration 1)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services.mandi_data_service import (
    get_latest_mandi_prices,
    get_commodity_summary,
    add_mandi_price_record,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/mandi-prices", response_model=List[schemas.MandiPriceRecordOut])
def list_mandi_prices(
    commodity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Fetch historical wholesale mandi price records, optionally filtered by commodity."""
    return get_latest_mandi_prices(db, commodity=commodity, limit=limit)


@router.get("/summary/{commodity}")
def commodity_market_summary(
    commodity: str,
    db: Session = Depends(get_db),
):
    """Retrieve summarized price statistics and moving averages for a commodity."""
    summary = get_commodity_summary(db, commodity=commodity)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No mandi price history found for commodity: {commodity}",
        )
    return summary


@router.post("/mandi-prices", response_model=schemas.MandiPriceRecordOut, status_code=status.HTTP_201_CREATED)
def record_mandi_price(
    payload: schemas.MandiPriceCreate,
    db: Session = Depends(get_db),
):
    """Insert a new validated mandi benchmark record."""
    return add_mandi_price_record(db, payload)
