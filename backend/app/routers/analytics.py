"""
Analytics & Market Intelligence Router
Primary Maintainer: Swyam Shukla (Database Lead & API Integration 1)
Extended for Phase 3:
  - Geographical District and Mandi Cascading Discovery
  - 90-Day Rolling Window Historical Mandi Prices with Quintal/Kg Conversions
  - Market Price Trend Summary & Descriptive Moving Averages
  - Deterministic Farmer Selling-Price Guidance (Q1-Q3 Percentiles)
  - Admin-Authorized Official CSV Data Ingestion & Audit Report
  - Mandi Platform Integration Status & Cache Freshness Diagnostics
"""

from typing import List, Optional, Union
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..database import get_db
from ..utils.security import get_current_user, require_role
from ..services.mandi_data_service import (
    get_available_states,
    get_available_districts,
    get_available_mandis,
    get_mandi_price_history,
    get_mandi_summary_analytics,
    calculate_selling_price_guidance,
    import_mandi_csv_data,
    get_mandi_platform_status,
    add_mandi_price_record,
    get_latest_mandi_prices,
)
from ..services.mandi_normalizer import normalize_commodity, CANONICAL_COMMODITIES, parse_arrival_date

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================
# 1. GEOGRAPHICAL DISCOVERY ENDPOINTS
# ============================================================

@router.get("/locations/states", response_model=List[str])
def list_states(db: Session = Depends(get_db)):
    """Retrieve all distinct Indian states currently available in Mandi benchmarks."""
    return get_available_states(db)


@router.get("/locations/districts", response_model=List[str])
def list_districts(
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve all distinct Indian districts, optionally filtered by state."""
    return get_available_districts(db, state=state)


@router.get("/locations/mandis", response_model=List[str])
def list_mandis(
    state: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve available APMC mandis, dynamically cascading from the selected state and district."""
    return get_available_mandis(db, state=state, district=district)


# ============================================================
# 2. HISTORICAL MANDI PRICES (STRICT 90-DAY WINDOW)
# ============================================================

@router.get("/mandi-prices", response_model=Union[schemas.MandiPriceHistoryOut, List[schemas.MandiPriceRecordOut]])
def list_mandi_prices(
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    commodity: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=1000),
    format: Optional[str] = "history",
    db: Session = Depends(get_db),
):
    """
    Retrieve historical wholesale mandi prices within a rolling 90-day window.
    Applies on-demand sync, canonical normalization, strict date filtering, and unit conversion (Quintal <-> Kg).
    """
    now_utc = datetime.now(timezone.utc)
    max_history_days = settings.mandi_history_days
    earliest_allowed = (now_utc.date() - timedelta(days=max_history_days)).strftime("%Y-%m-%d")

    # Validate date parameters
    if from_date:
        parsed_from = parse_arrival_date(from_date)
        if not parsed_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid 'from_date' format: '{from_date}'. Expected ISO format YYYY-MM-DD.",
            )
        if parsed_from < earliest_allowed:
            from_date = earliest_allowed
        else:
            from_date = parsed_from

    if to_date:
        parsed_to = parse_arrival_date(to_date)
        if not parsed_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid 'to_date' format: '{to_date}'. Expected ISO format YYYY-MM-DD.",
            )
        to_date = parsed_to

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'from_date' ({from_date}) cannot be after 'to_date' ({to_date}).",
        )

    # Normalize limit if invoked directly in unit tests
    num_limit = limit.default if hasattr(limit, "default") and not isinstance(limit, int) else int(limit)

    history = get_mandi_price_history(
        db=db,
        state=state,
        district=district,
        market=market,
        commodity=commodity,
        from_date=from_date,
        to_date=to_date,
        limit=num_limit,
    )
    if format == "list":
        return history["records"]

    return schemas.MandiPriceHistoryOut(**history)


# ============================================================
# 3. MARKET SUMMARY & DESCRIPTIVE TRENDS
# ============================================================

@router.get("/summary", response_model=schemas.MandiSummaryOut)
def market_summary(
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    commodity: str = "Tomato",
    db: Session = Depends(get_db),
):
    """
    Retrieve summarized price statistics, moving averages, and trend direction for a commodity
    at the selected district or APMC market strictly over the 90-day historical window.
    """
    summary = get_mandi_summary_analytics(db, state=state, district=district, market=market, commodity=commodity)
    if not summary:
        loc_desc = market or district or state or "selected location"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No mandi price history found for commodity '{commodity}' in {loc_desc} within the last 90 days.",
        )
    return schemas.MandiSummaryOut(**summary)


@router.get("/summary/{commodity}", response_model=schemas.MandiSummaryOut)
def commodity_market_summary_legacy(
    commodity: str,
    db: Session = Depends(get_db),
):
    """Legacy endpoint: Retrieve summarized price statistics and moving averages for a commodity."""
    summary = get_mandi_summary_analytics(db, commodity=commodity)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No mandi price history found for commodity: {commodity} within the last 90 days.",
        )
    return schemas.MandiSummaryOut(**summary)


# ============================================================
# 4. FARMER SELLING-PRICE GUIDANCE
# ============================================================

@router.get("/selling-price-guidance", response_model=schemas.SellingPriceGuidanceOut)
def get_selling_price_guidance(
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    FARMER SELLING-PRICE GUIDANCE:
      Calculates an indicative market-based price interval (25th to 75th percentile)
      in INR/kg from valid 90-day historical modal prices from the selected market.
      Explicitly non-binding guidance; farmer retains complete pricing control.
    """
    guidance = calculate_selling_price_guidance(
        db=db,
        commodity=commodity,
        state=state,
        district=district,
        market=market,
    )
    return schemas.SellingPriceGuidanceOut(**guidance)


# ============================================================
# 5. ADMIN MANUAL CSV DATA IMPORT & AUDIT
# ============================================================

@router.post("/mandi-prices/import", response_model=schemas.MandiCSVImportResult, status_code=status.HTTP_201_CREATED)
async def import_mandi_csv(
    file: UploadFile = File(..., description="Official Mandi Price CSV export file"),
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_role(models.UserRole.admin)),
):
    """
    ADMINISTRATOR MANUAL CSV INGESTION:
      Upload an official Agmarknet / Mandi CSV file.
      Validates file size (max 5MB), UTF-8 BOM encoding, schema, price bounds,
      and performs atomic deduplication and upsert.
      Protected: Administrator access only.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only official .csv files are supported for mandi data import.",
        )

    max_bytes = settings.mandi_csv_max_size_mb * 1024 * 1024
    content_bytes = await file.read(max_bytes + 1)
    if len(content_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"CSV upload exceeds maximum allowed file size of {settings.mandi_csv_max_size_mb} MB.",
        )

    # Handle UTF-8 with BOM (utf-8-sig), standard utf-8, and latin-1
    try:
        csv_text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            csv_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                csv_text = content_bytes.decode("latin-1")
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not decode CSV file. Please ensure standard UTF-8 encoding.",
                )

    result = import_mandi_csv_data(db, csv_content=csv_text, filename=file.filename)
    return schemas.MandiCSVImportResult(**result)


# ============================================================
# 6. PLATFORM STATUS & CACHE DIAGNOSTICS
# ============================================================

@router.get("/status", response_model=schemas.MandiStatusOut)
def mandi_platform_status(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin, models.UserRole.reviewer)),
):
    """Retrieve operational diagnostics for Mandi integration, cache TTL, and ingestion logs (Admin/Reviewer)."""
    diag = get_mandi_platform_status(db)
    return schemas.MandiStatusOut(**diag)


# ============================================================
# 7. BACKWARD COMPATIBLE INSERT ENDPOINT
# ============================================================

@router.post("/mandi-prices", response_model=schemas.MandiPriceRecordOut, status_code=status.HTTP_201_CREATED)
def record_mandi_price(
    payload: schemas.MandiPriceCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin)),
):
    """Insert a single validated mandi benchmark record (Admin only)."""
    return add_mandi_price_record(db, payload)
Displaying analytics.py.
