"""
FarmCart Mandi Price Data Service
Primary Maintainer: Swyam Shukla (Database Lead)
Extended for Phase 3:
  - On-Demand API Ingestion with Transparent TTL Caching & Failure Cooldown
  - Graceful Stale-Cache Fallback on Upstream Failure without Data Erasure
  - Multi-State / Multi-District / Mandi Hierarchical Discovery
  - Strict 90-Day Rolling Window Analytics & Unit Conversions (Quintal <-> Kg)
  - Single-Mandi Deterministic Selling-Price Guidance (Q1-Q3 Percentiles)
  - Admin-Authorized Official CSV Data Ingestion, Row/Size Limits & Deduplication
"""

import csv
import io
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from .. import models, schemas
from ..config import settings
from .mandi_normalizer import (
    CANONICAL_COMMODITIES,
    normalize_commodity,
    parse_arrival_date,
    clean_location_name,
    validate_mandi_record,
)
from .ogd_client import (
    fetch_ogd_records,
    is_ogd_configured,
    OGDError,
    OGDNotConfiguredError,
    OGDTimeoutError,
    OGDRateLimitError,
)

logger = logging.getLogger("farmcart.mandi_service")


# ============================================================
# 1. GEOGRAPHICAL DISCOVERY: STATES, DISTRICTS & MANDIS
# ============================================================

def get_available_states(db: Session) -> List[str]:
    """Retrieve unique sorted list of Indian states with recorded mandi data."""
    results = (
        db.query(models.MandiPriceRecord.state)
        .distinct()
        .order_by(models.MandiPriceRecord.state.asc())
        .all()
    )
    return [r[0] for r in results if r[0] and r[0].strip()]


def get_available_districts(db: Session, state: Optional[str] = None) -> List[str]:
    """Retrieve unique sorted list of districts, optionally filtered by state."""
    query = db.query(models.MandiPriceRecord.district).distinct()
    if state and state.strip() and state.strip().lower() not in ("all", "all states", "india"):
        clean_state = clean_location_name(state)
        query = query.filter(func.lower(models.MandiPriceRecord.state) == clean_state.lower())
    results = query.order_by(models.MandiPriceRecord.district.asc()).all()
    return [r[0] for r in results if r[0] and r[0].strip()]


def get_available_mandis(
    db: Session,
    state: Optional[str] = None,
    district: Optional[str] = None,
) -> List[str]:
    """Retrieve unique sorted list of APMC mandis, optionally filtered by state and district."""
    query = db.query(models.MandiPriceRecord.market).distinct()
    if state and state.strip() and state.strip().lower() not in ("all", "all states", "india"):
        clean_state = clean_location_name(state)
        query = query.filter(func.lower(models.MandiPriceRecord.state) == clean_state.lower())
    if district and district.strip() and district.strip().lower() not in ("all", "all districts"):
        clean_dist = clean_location_name(district)
        query = query.filter(func.lower(models.MandiPriceRecord.district) == clean_dist.lower())
    results = query.order_by(models.MandiPriceRecord.market.asc()).all()
    return [r[0] for r in results if r[0] and r[0].strip()]


# ============================================================
# 2. ON-DEMAND SYNC, CACHE FRESHNESS & COOLDOWN
# ============================================================

def get_cache_metadata(
    db: Session,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    commodity: Optional[str] = None,
) -> Optional[models.MandiCacheMetadata]:
    """Fetch cache metadata record for a specific geographic & commodity scope."""
    state_key = clean_location_name(state) if state and state.strip().lower() not in ("all", "all states", "india") else "All"
    dist_key = clean_location_name(district) if district and district.strip().lower() not in ("all", "all districts") else "All"
    mkt_key = clean_location_name(market) if market and market.strip().lower() not in ("all", "all mandis", "all markets") else "All"
    comm_key = normalize_commodity(commodity) or (commodity.title() if commodity and commodity.strip().lower() != "all" else "All")

    return (
        db.query(models.MandiCacheMetadata)
        .filter(
            models.MandiCacheMetadata.state == state_key,
            models.MandiCacheMetadata.district == dist_key,
            models.MandiCacheMetadata.market == mkt_key,
            models.MandiCacheMetadata.commodity == comm_key,
        )
        .first()
    )


def is_cache_fresh(metadata: Optional[models.MandiCacheMetadata]) -> bool:
    """Return True if cache record exists, succeeded, and is within the configured TTL window."""
    if not metadata or metadata.status != "success":
        return False

    fetch_time = metadata.last_successful_fetch_at or metadata.last_fetched_at
    if not fetch_time:
        return False

    now_utc = datetime.now(timezone.utc)
    if fetch_time.tzinfo is None:
        fetch_time = fetch_time.replace(tzinfo=timezone.utc)

    max_age = timedelta(hours=settings.mandi_cache_ttl_hours)
    return (now_utc - fetch_time) <= max_age


def is_cooldown_active(metadata: Optional[models.MandiCacheMetadata]) -> bool:
    """Return True if repeated upstream failure cooldown is currently in effect."""
    if not metadata or not metadata.cooldown_until:
        return False

    now_utc = datetime.now(timezone.utc)
    cd_time = metadata.cooldown_until
    if cd_time.tzinfo is None:
        cd_time = cd_time.replace(tzinfo=timezone.utc)

    return now_utc < cd_time


def sync_mandi_data_on_demand(
    db: Session,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    commodity: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    On-Demand Ingestion Workflow:
      1. Check existing cached metadata for (state, district, market, commodity).
      2. If fresh, return cache hit without issuing external HTTP call.
      3. If failure cooldown is active, suppress retry to avoid hammering upstream.
      4. Query official OGD API resource with state-aware parameters.
      5. Normalize and validate upstream records.
      6. Upsert records into mandi_price_records without duplicates.
      7. Record last_successful_fetch_at and clear cooldown on success.
      8. On upstream failure: record last_attempted_at, set failure cooldown,
         preserve previous last_successful_fetch_at and cached historical records.
    Returns: (success: bool, status_msg: str)
    """
    state_str = str(state).strip() if isinstance(state, str) and state.strip() else None
    dist_str = str(district).strip() if isinstance(district, str) and district.strip() else None
    mkt_str = str(market).strip() if isinstance(market, str) and market.strip() else None
    comm_str = str(commodity).strip() if isinstance(commodity, str) and commodity.strip() else None

    canonical_comm = normalize_commodity(comm_str) if comm_str else None
    state_key = clean_location_name(state_str) if state_str and state_str.lower() not in ("all", "all states", "india") else "All"
    dist_key = clean_location_name(dist_str) if dist_str and dist_str.lower() not in ("all", "all districts") else "All"
    mkt_key = clean_location_name(mkt_str) if mkt_str and mkt_str.lower() not in ("all", "all mandis", "all markets") else "All"
    comm_key = canonical_comm or (comm_str.title() if comm_str and comm_str.lower() != "all" else "All")

    metadata = get_cache_metadata(db, state=state_str, district=dist_str, market=mkt_str, commodity=comm_str)

    if is_cache_fresh(metadata):
        logger.debug("Cache hit for scope (%s, %s, %s, %s); skipping upstream fetch", state_key, dist_key, mkt_key, comm_key)
        return True, "cache_hit"

    # Check failure retry cooldown suppression
    if is_cooldown_active(metadata):
        logger.info("Failure cooldown active for scope (%s, %s, %s, %s); serving stale cache", state_key, dist_key, mkt_key, comm_key)
        return False, "cooldown_active"

    now_utc = datetime.now(timezone.utc)

    # Upstream fetch execution
    try:
        raw_records = fetch_ogd_records(
            state=state_str if state_key != "All" else None,
            district=dist_str if dist_key != "All" else None,
            market=mkt_str if mkt_key != "All" else None,
            commodity=canonical_comm,
            limit=500,
        )
    except OGDNotConfiguredError as cfg_err:
        logger.info("OGD unconfigured: %s", cfg_err)
        return False, "ogd_unconfigured"
    except (OGDError, Exception) as ogd_err:
        logger.warning("Upstream OGD query failed for (%s, %s, %s, %s): %s", state_key, dist_key, mkt_key, comm_key, ogd_err)
        cooldown_target = now_utc + timedelta(minutes=settings.mandi_failure_cooldown_minutes)

        try:
            if not metadata:
                metadata = models.MandiCacheMetadata(
                    state=state_key,
                    district=dist_key,
                    market=mkt_key,
                    commodity=comm_key,
                    last_fetched_at=None,
                    last_successful_fetch_at=None,
                    last_attempted_at=now_utc,
                    status="failed",
                    record_count=0,
                    last_successful_record_count=0,
                    error_message=str(ogd_err),
                    cooldown_until=cooldown_target,
                    source="ogd_api",
                )
                db.add(metadata)
            else:
                metadata.status = "failed"
                metadata.last_attempted_at = now_utc
                metadata.error_message = str(ogd_err)
                metadata.cooldown_until = cooldown_target
                metadata.updated_at = now_utc

            db.commit()
        except Exception as db_err:
            db.rollback()
            logger.error("Failed to commit cache failure state: %s", db_err)

        return False, f"upstream_failed: {ogd_err}"

    # Upsert validated records
    inserted_count = 0
    try:
        for item in raw_records:
            norm_rec, error_msg = validate_mandi_record(item)
            if not norm_rec:
                continue

            existing = (
                db.query(models.MandiPriceRecord)
                .filter(
                    models.MandiPriceRecord.state == norm_rec["state"],
                    models.MandiPriceRecord.district == norm_rec["district"],
                    models.MandiPriceRecord.market == norm_rec["market"],
                    models.MandiPriceRecord.commodity == norm_rec["commodity"],
                    models.MandiPriceRecord.variety == norm_rec["variety"],
                    models.MandiPriceRecord.arrival_date == norm_rec["arrival_date"],
                )
                .first()
            )

            if existing:
                existing.min_price = norm_rec["min_price"]
                existing.max_price = norm_rec["max_price"]
                existing.modal_price = norm_rec["modal_price"]
                existing.arrivals_ton = norm_rec["arrivals_ton"]
                existing.source = "ogd_api"
                existing.fetched_at = now_utc
            else:
                new_record = models.MandiPriceRecord(
                    state=norm_rec["state"],
                    district=norm_rec["district"],
                    market=norm_rec["market"],
                    commodity=norm_rec["commodity"],
                    variety=norm_rec["variety"],
                    arrival_date=norm_rec["arrival_date"],
                    min_price=norm_rec["min_price"],
                    max_price=norm_rec["max_price"],
                    modal_price=norm_rec["modal_price"],
                    arrivals_ton=norm_rec["arrivals_ton"],
                    source="ogd_api",
                    fetched_at=now_utc,
                )
                db.add(new_record)
                inserted_count += 1

        # Update cache metadata on success
        if not metadata:
            metadata = models.MandiCacheMetadata(
                state=state_key,
                district=dist_key,
                market=mkt_key,
                commodity=comm_key,
                last_fetched_at=now_utc,
                last_successful_fetch_at=now_utc,
                last_attempted_at=now_utc,
                status="success",
                record_count=len(raw_records),
                last_successful_record_count=len(raw_records),
                error_message=None,
                cooldown_until=None,
                source="ogd_api",
            )
            db.add(metadata)
        else:
            metadata.last_fetched_at = now_utc
            metadata.last_successful_fetch_at = now_utc
            metadata.last_attempted_at = now_utc
            metadata.status = "success"
            metadata.record_count = len(raw_records)
            metadata.last_successful_record_count = len(raw_records)
            metadata.error_message = None
            metadata.cooldown_until = None
            metadata.updated_at = now_utc

        db.commit()
    except Exception as commit_err:
        db.rollback()
        logger.error("Database transaction rolled back during mandi sync: %s", commit_err)
        return False, f"database_error: {commit_err}"

    return True, f"synced_{len(raw_records)}_records"


# ============================================================
# 3. HISTORICAL MANDI DATA RETRIEVAL (STRICT 90-DAY WINDOW)
# ============================================================

def get_mandi_price_history(
    db: Session,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    commodity: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 200,
) -> Dict[str, Any]:
    """
    Retrieve historical mandi price records within a strict 90-day rolling window.
    Enforces normalized exact location matching, safe limit bounds, and unit conversions.
    """
    canonical_comm = normalize_commodity(commodity) if commodity else None

    # Trigger on-demand sync
    sync_mandi_data_on_demand(db, state=state, district=district, market=market, commodity=canonical_comm)

    now_utc = datetime.now(timezone.utc)
    max_days = settings.mandi_history_days
    cutoff_dt = now_utc.date() - timedelta(days=max_days)
    cutoff_date_str = cutoff_dt.strftime("%Y-%m-%d")
    today_str = now_utc.date().strftime("%Y-%m-%d")

    # Strict window clamping
    req_from = parse_arrival_date(from_date) if from_date else cutoff_date_str
    req_to = parse_arrival_date(to_date) if to_date else today_str

    if not req_from or req_from < cutoff_date_str:
        req_from = cutoff_date_str
    if not req_to:
        req_to = today_str

    query = db.query(models.MandiPriceRecord)
    if canonical_comm:
        query = query.filter(models.MandiPriceRecord.commodity == canonical_comm)

    if state and state.strip() and state.strip().lower() not in ("all", "all states", "india"):
        clean_state = clean_location_name(state)
        query = query.filter(func.lower(models.MandiPriceRecord.state) == clean_state.lower())

    if district and district.strip() and district.strip().lower() not in ("all", "all districts"):
        clean_dist = clean_location_name(district)
        query = query.filter(func.lower(models.MandiPriceRecord.district) == clean_dist.lower())

    if market and market.strip() and market.strip().lower() not in ("all", "all mandis", "all markets"):
        clean_mkt = clean_location_name(market)
        query = query.filter(func.lower(models.MandiPriceRecord.market) == clean_mkt.lower())

    # Strict date range filter
    query = query.filter(
        models.MandiPriceRecord.arrival_date >= req_from,
        models.MandiPriceRecord.arrival_date <= req_to,
    )

    # Ensure safe limit handling if called directly with Query default object
    if hasattr(limit, "default") and not isinstance(limit, int):
        actual_limit = int(limit.default)
    else:
        try:
            actual_limit = int(limit)
        except (ValueError, TypeError):
            actual_limit = 200

    safe_limit = max(1, min(actual_limit, 1000))
    records = query.order_by(models.MandiPriceRecord.arrival_date.desc()).limit(safe_limit).all()

    # Determine freshness metadata
    metadata = get_cache_metadata(db, state=state, district=district, market=market, commodity=canonical_comm or commodity)
    is_stale = not is_cache_fresh(metadata)
    last_fetched = metadata.last_successful_fetch_at or metadata.last_fetched_at if metadata else None
    last_attempted = metadata.last_attempted_at if metadata else None

    # Format output records with both Quintal and Kg units
    formatted = []
    for r in records:
        out = schemas.MandiPriceRecordOut.model_validate(r)
        out.modal_price_kg = round(r.modal_price / 100.0, 2)
        out.min_price_kg = round(r.min_price / 100.0, 2)
        out.max_price_kg = round(r.max_price / 100.0, 2)
        formatted.append(out)

    earliest = records[-1].arrival_date if records else None
    latest = records[0].arrival_date if records else None

    return {
        "records": formatted,
        "total_count": len(formatted),
        "commodity": canonical_comm or (commodity or "All"),
        "state": state,
        "district": district,
        "market": market,
        "earliest_date": earliest,
        "latest_date": latest,
        "is_stale": is_stale,
        "source": metadata.source if metadata else (records[0].source if records else "seed"),
        "last_fetched_at": last_fetched,
        "last_successful_fetch_at": last_fetched,
        "last_attempted_at": last_attempted,
    }


# ============================================================
# 4. SUMMARY ANALYTICS & SINGLE-MANDI PRICE TRENDS
# ============================================================

def get_mandi_summary_analytics(
    db: Session,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    commodity: str = "Tomato",
) -> Optional[Dict[str, Any]]:
    """
    Compute descriptive market summary metrics strictly over the 90-day window:
      - Latest modal, min, max price (Quintal and Kg)
      - 7-observation moving average of actual trading observations
      - Absolute & percentage price change
      - Descriptive trend indication (upward, downward, stable)
      - Strictly isolated to the selected mandi scope (no accidental pooling)
      - Never includes records outside the 90-day historical boundary
    """
    canonical_comm = normalize_commodity(commodity) or commodity.title()

    # Trigger on-demand sync
    sync_mandi_data_on_demand(db, state=state, district=district, market=market, commodity=canonical_comm)

    now_utc = datetime.now(timezone.utc)
    cutoff_date = (now_utc.date() - timedelta(days=settings.mandi_history_days)).strftime("%Y-%m-%d")

    query = db.query(models.MandiPriceRecord).filter(
        models.MandiPriceRecord.commodity == canonical_comm,
        models.MandiPriceRecord.arrival_date >= cutoff_date,
    )

    if state and state.strip() and state.strip().lower() not in ("all", "all states", "india"):
        clean_state = clean_location_name(state)
        query = query.filter(func.lower(models.MandiPriceRecord.state) == clean_state.lower())

    if district and district.strip() and district.strip().lower() not in ("all", "all districts"):
        clean_dist = clean_location_name(district)
        query = query.filter(func.lower(models.MandiPriceRecord.district) == clean_dist.lower())

    if market and market.strip() and market.strip().lower() not in ("all", "all mandis", "all markets"):
        clean_mkt = clean_location_name(market)
        query = query.filter(func.lower(models.MandiPriceRecord.market) == clean_mkt.lower())

    # Order ascending by date for chronological trend & moving average calculation
    records = query.order_by(models.MandiPriceRecord.arrival_date.asc()).all()

    # STRICT 90-DAY REQUIREMENT: If no observations exist within 90 days, return None
    # Never fall back to older historical data outside the window
    if not records:
        return None

    modal_prices = [r.modal_price for r in records]
    n = len(modal_prices)

    latest_rec = records[-1]
    earliest_rec = records[0]

    earliest_p = modal_prices[0]
    latest_p = modal_prices[-1]
    pct_change = round(((latest_p - earliest_p) / earliest_p) * 100.0, 2) if earliest_p > 0 else 0.0

    if pct_change > 1.0:
        trend_direction = "upward"
    elif pct_change < -1.0:
        trend_direction = "downward"
    else:
        trend_direction = "stable"

    # 7-observation moving average (based on trading observations, not calendar days)
    window = modal_prices[-7:] if n >= 7 else modal_prices
    ma_7 = sum(window) / len(window)

    hist_min = min(r.min_price for r in records)
    hist_max = max(r.max_price for r in records)

    daily_series = []
    for r in records:
        daily_series.append(schemas.MandiDailyPoint(
            date=r.arrival_date,
            modal_price_quintal=round(r.modal_price, 2),
            modal_price_kg=round(r.modal_price / 100.0, 2),
            min_price_quintal=round(r.min_price, 2),
            max_price_quintal=round(r.max_price, 2),
            arrivals_ton=round(r.arrivals_ton, 2),
        ))

    metadata = get_cache_metadata(db, state=state, district=district, market=market, commodity=canonical_comm)
    is_stale = not is_cache_fresh(metadata)
    last_fetched = metadata.last_successful_fetch_at or metadata.last_fetched_at if metadata else None
    last_attempted = metadata.last_attempted_at if metadata else None
    data_source = metadata.source if metadata else (latest_rec.source or "seed")

    return {
        "commodity": commodity,
        "canonical_commodity": canonical_comm,
        "state": state or latest_rec.state,
        "district": district or latest_rec.district,
        "market": market or latest_rec.market,
        "latest_arrival_date": latest_rec.arrival_date,
        "latest_modal_quintal": round(latest_rec.modal_price, 2),
        "latest_modal_kg": round(latest_rec.modal_price / 100.0, 2),
        "latest_min_quintal": round(latest_rec.min_price, 2),
        "latest_min_kg": round(latest_rec.min_price / 100.0, 2),
        "latest_max_quintal": round(latest_rec.max_price, 2),
        "latest_max_kg": round(latest_rec.max_price / 100.0, 2),
        "moving_average_kg": round(ma_7 / 100.0, 2),
        "moving_average_label": "7-observation moving average",
        "historical_min_quintal": round(hist_min, 2),
        "historical_max_quintal": round(hist_max, 2),
        "historical_min_kg": round(hist_min / 100.0, 2),
        "historical_max_kg": round(hist_max / 100.0, 2),
        "price_change_pct": pct_change,
        "trend_direction": trend_direction,
        "sample_days": n,
        "date_range_start": earliest_rec.arrival_date,
        "date_range_end": latest_rec.arrival_date,
        "daily_series": daily_series,
        "is_stale": is_stale,
        "data_source": data_source,
        "last_fetched_at": last_fetched,
        "last_successful_fetch_at": last_fetched,
        "last_attempted_at": last_attempted,
    }


# ============================================================
# 5. FARMER SELLING-PRICE GUIDANCE (STRICT SINGLE-MANDI Q1-Q3)
# ============================================================

def _compute_percentiles(prices: List[float]) -> Tuple[float, float]:
    """Calculate 25th percentile (Q1) and 75th percentile (Q3) of sorted prices via linear interpolation."""
    if not prices:
        return 0.0, 0.0
    sorted_p = sorted(prices)
    n = len(sorted_p)
    if n == 1:
        return sorted_p[0], sorted_p[0]

    def _calc(arr, p):
        k = (len(arr) - 1) * p
        f = int(k)
        c = f + 1 if f + 1 < len(arr) else f
        weight = k - f
        return arr[f] * (1.0 - weight) + arr[c] * weight

    return round(_calc(sorted_p, 0.25), 2), round(_calc(sorted_p, 0.75), 2)


def calculate_selling_price_guidance(
    db: Session,
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Farmer Selling-Price Guidance Engine:
      - Uses records strictly from the selected mandi scope (no cross-mandi fallback).
      - Respects the strict 90-day historical window.
      - Requires at least 3 valid observations; returns explicit insufficient result otherwise.
      - Calculates Q1 (25th) and Q3 (75th) percentiles of modal prices.
      - Converts from INR/quintal to INR/kg (/ 100).
      - Explicit non-binding guidance disclaimer; farmer retains complete price control.
    """
    canonical_comm = normalize_commodity(commodity)
    if not canonical_comm:
        return {
            "commodity": commodity,
            "canonical_commodity": "Unknown",
            "state": state,
            "district": district,
            "market": market,
            "is_sufficient": False,
            "reason_if_insufficient": f"Commodity '{commodity}' is not among the supported categories ({', '.join(sorted(CANONICAL_COMMODITIES))}).",
            "sample_observations": 0,
            "date_window_days": settings.mandi_history_days,
            "disclaimer": "Indicative market-based price guidance — not a guaranteed selling price. Farmer retains complete control.",
        }

    # Trigger on-demand sync for scope
    sync_mandi_data_on_demand(db, state=state, district=district, market=market, commodity=canonical_comm)

    now_utc = datetime.now(timezone.utc)
    cutoff_date = (now_utc.date() - timedelta(days=settings.mandi_history_days)).strftime("%Y-%m-%d")

    query = db.query(models.MandiPriceRecord).filter(
        models.MandiPriceRecord.commodity == canonical_comm,
        models.MandiPriceRecord.arrival_date >= cutoff_date,
    )

    if state and state.strip() and state.strip().lower() not in ("all", "all states", "india"):
        clean_state = clean_location_name(state)
        query = query.filter(func.lower(models.MandiPriceRecord.state) == clean_state.lower())

    if district and district.strip() and district.strip().lower() not in ("all", "all districts"):
        clean_dist = clean_location_name(district)
        query = query.filter(func.lower(models.MandiPriceRecord.district) == clean_dist.lower())

    if market and market.strip() and market.strip().lower() not in ("all", "all mandis", "all markets"):
        clean_mkt = clean_location_name(market)
        query = query.filter(func.lower(models.MandiPriceRecord.market) == clean_mkt.lower())

    records = query.order_by(models.MandiPriceRecord.arrival_date.asc()).all()

    # STRICT SINGLE-MANDI SCOPE: No fallback to other mandis or nationwide records
    if len(records) < 3:
        loc_desc = market or district or state or "selected location"
        return {
            "commodity": commodity,
            "canonical_commodity": canonical_comm,
            "state": state,
            "district": district,
            "market": market,
            "is_sufficient": False,
            "reason_if_insufficient": f"Insufficient historical data in {loc_desc} ({len(records)} observations found; minimum 3 required to compute reliable price guidance within the 90-day window).",
            "sample_observations": len(records),
            "date_window_days": settings.mandi_history_days,
            "disclaimer": "Indicative market-based price guidance — not a guaranteed selling price. Farmer retains complete control.",
        }

    modal_prices = [r.modal_price for r in records]
    q1_quintal, q3_quintal = _compute_percentiles(modal_prices)

    q1_kg = round(q1_quintal / 100.0, 2)
    q3_kg = round(q3_quintal / 100.0, 2)
    latest_modal_kg = round(records[-1].modal_price / 100.0, 2)

    return {
        "commodity": commodity,
        "canonical_commodity": canonical_comm,
        "state": state or records[-1].state,
        "district": district or records[-1].district,
        "market": market or records[-1].market,
        "is_sufficient": True,
        "reason_if_insufficient": None,
        "sample_observations": len(records),
        "date_window_days": settings.mandi_history_days,
        "earliest_observation": records[0].arrival_date,
        "latest_observation": records[-1].arrival_date,
        "q1_quintal": q1_quintal,
        "q3_quintal": q3_quintal,
        "suggested_min_price_kg": q1_kg,
        "suggested_max_price_kg": q3_kg,
        "prevailing_modal_price_kg": latest_modal_kg,
        "disclaimer": "Indicative market-based price guidance — not a guaranteed selling price. Farmer retains complete control.",
    }


# ============================================================
# 6. ADMIN OFFICIAL CSV DATA IMPORT (HARDENED)
# ============================================================

REQUIRED_CSV_FIELDS = {"commodity", "arrival_date", "min_price", "max_price", "modal_price"}

def import_mandi_csv_data(
    db: Session,
    csv_content: str,
    filename: str,
) -> Dict[str, Any]:
    """
    Administrator Manual CSV Ingestion:
      1. Validates encoding, header existence and schema completeness.
      2. Enforces maximum row limits from configuration.
      3. Validates price positivity, finite numbers, price consistency, and commodity mapping.
      4. Detects duplicates on natural key and performs atomic upsert.
      5. Wraps in atomic database transaction with automatic rollback on error.
      6. Returns comprehensive metrics: inserted, updated, skipped, rejected, error details.
    """
    now_utc = datetime.now(timezone.utc)
    max_rows = settings.mandi_csv_max_rows

    try:
        reader = csv.DictReader(io.StringIO(csv_content))
    except Exception as read_err:
        return {
            "success": False,
            "filename": filename,
            "total_rows": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "rejected": 0,
            "errors": [f"CSV parse error: {read_err}"],
            "imported_at": now_utc,
        }

    if not reader.fieldnames:
        return {
            "success": False,
            "filename": filename,
            "total_rows": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "rejected": 0,
            "errors": ["CSV file is empty or missing a valid header row."],
            "imported_at": now_utc,
        }

    # Normalize header names (lowercase, strip BOM and spaces)
    normalized_headers = {h.strip().lower().lstrip("\ufeff"): h for h in reader.fieldnames if h}

    total_rows = 0
    inserted = 0
    updated = 0
    skipped = 0
    rejected = 0
    errors: List[str] = []

    try:
        for row_idx, row in enumerate(reader, start=1):
            if total_rows >= max_rows:
                errors.append(f"Upload row limit exceeded: Stopped processing at row {max_rows} (maximum permitted: {max_rows}).")
                break

            total_rows += 1
            # Clean keys
            clean_row = {k.strip().lower().lstrip("\ufeff"): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k}
            norm_rec, error_reason = validate_mandi_record(clean_row)

            if not norm_rec:
                rejected += 1
                if len(errors) < 25:
                    errors.append(f"Row {row_idx}: {error_reason}")
                continue

            # Natural key uniqueness check
            existing = (
                db.query(models.MandiPriceRecord)
                .filter(
                    models.MandiPriceRecord.state == norm_rec["state"],
                    models.MandiPriceRecord.district == norm_rec["district"],
                    models.MandiPriceRecord.market == norm_rec["market"],
                    models.MandiPriceRecord.commodity == norm_rec["commodity"],
                    models.MandiPriceRecord.variety == norm_rec["variety"],
                    models.MandiPriceRecord.arrival_date == norm_rec["arrival_date"],
                )
                .first()
            )

            if existing:
                if (
                    abs(existing.min_price - norm_rec["min_price"]) < 0.01
                    and abs(existing.max_price - norm_rec["max_price"]) < 0.01
                    and abs(existing.modal_price - norm_rec["modal_price"]) < 0.01
                ):
                    skipped += 1
                else:
                    existing.min_price = norm_rec["min_price"]
                    existing.max_price = norm_rec["max_price"]
                    existing.modal_price = norm_rec["modal_price"]
                    existing.arrivals_ton = norm_rec["arrivals_ton"]
                    existing.source = "csv_import"
                    existing.fetched_at = now_utc
                    updated += 1
            else:
                new_rec = models.MandiPriceRecord(
                    state=norm_rec["state"],
                    district=norm_rec["district"],
                    market=norm_rec["market"],
                    commodity=norm_rec["commodity"],
                    variety=norm_rec["variety"],
                    arrival_date=norm_rec["arrival_date"],
                    min_price=norm_rec["min_price"],
                    max_price=norm_rec["max_price"],
                    modal_price=norm_rec["modal_price"],
                    arrivals_ton=norm_rec["arrivals_ton"],
                    source="csv_import",
                    fetched_at=now_utc,
                )
                db.add(new_rec)
                inserted += 1

        db.commit()

    except Exception as tx_err:
        db.rollback()
        logger.error("Transactional rollback in CSV import: %s", tx_err)
        return {
            "success": False,
            "filename": filename,
            "total_rows": total_rows,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "rejected": total_rows,
            "errors": [f"Database transaction failure: {tx_err}. All changes were rolled back."],
            "imported_at": now_utc,
        }

    return {
        "success": True,
        "filename": filename,
        "total_rows": total_rows,
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "rejected": rejected,
        "errors": errors,
        "imported_at": now_utc,
    }


# ============================================================
# 7. PLATFORM MANDI STATUS & AUDIT INSPECTION
# ============================================================

def get_mandi_platform_status(db: Session) -> Dict[str, Any]:
    """Retrieve operational status of Mandi integration, cache counts, and logs."""
    total_records = db.query(models.MandiPriceRecord).count()

    commodity_counts = {}
    for comm in sorted(CANONICAL_COMMODITIES):
        cnt = db.query(models.MandiPriceRecord).filter(models.MandiPriceRecord.commodity == comm).count()
        commodity_counts[comm] = cnt

    recent_metadata = (
        db.query(models.MandiCacheMetadata)
        .order_by(models.MandiCacheMetadata.created_at.desc())
        .limit(10)
        .all()
    )
    fetches = []
    for m in recent_metadata:
        fetches.append({
            "state": m.state,
            "district": m.district,
            "market": m.market,
            "commodity": m.commodity,
            "status": m.status,
            "record_count": m.record_count,
            "last_successful_fetch_at": m.last_successful_fetch_at.isoformat() if m.last_successful_fetch_at else None,
            "last_attempted_at": m.last_attempted_at.isoformat() if m.last_attempted_at else None,
            "cooldown_until": m.cooldown_until.isoformat() if m.cooldown_until else None,
            "error_message": m.error_message,
        })

    return {
        "ogd_configured": is_ogd_configured(),
        "ogd_resource_uuid": settings.ogd_resource_uuid,
        "cache_ttl_hours": settings.mandi_cache_ttl_hours,
        "total_records": total_records,
        "commodity_counts": commodity_counts,
        "recent_fetches": fetches,
    }


# ============================================================
# 8. BACKWARD COMPATIBILITY HELPERS (PHASE 1 / 2)
# ============================================================

def get_latest_mandi_prices(
    db: Session,
    commodity: Optional[str] = None,
    limit: int = 50,
) -> List[models.MandiPriceRecord]:
    """Preserved Phase 1 legacy signature."""
    query = db.query(models.MandiPriceRecord)
    if commodity:
        canonical = normalize_commodity(commodity) or commodity
        query = query.filter(models.MandiPriceRecord.commodity == canonical)
    return query.order_by(models.MandiPriceRecord.arrival_date.desc()).limit(limit).all()


def get_commodity_summary(
    db: Session,
    commodity: str,
) -> Optional[Dict[str, Any]]:
    """Preserved Phase 1 legacy signature."""
    return get_mandi_summary_analytics(db, commodity=commodity)


def add_mandi_price_record(
    db: Session,
    payload: schemas.MandiPriceCreate,
) -> models.MandiPriceRecord:
    """Preserved Phase 1 legacy signature."""
    norm_rec, err = validate_mandi_record(payload.model_dump())
    if err:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    record = models.MandiPriceRecord(**norm_rec)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
