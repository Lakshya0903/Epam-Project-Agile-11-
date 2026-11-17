"""
Nationwide Serviceability & Delivery Zone Management Engine
Primary Maintainer: Hemant Yadav & Swyam Shukla
Phase 2: Validates Indian PIN codes, checks active DeliveryZones, and verifies
eligibility for Home Delivery and Shared Drop Points.
"""

import json
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..utils.geo import is_valid_indian_pincode, clean_pincode


def _parse_pincodes(raw_str: str) -> List[str]:
    """Parse JSON array or comma-separated PIN code list into cleaned list."""
    if not raw_str:
        return []
    raw_str = raw_str.strip()
    if raw_str.startswith("["):
        try:
            items = json.loads(raw_str)
            return [str(p).strip() for p in items if str(p).strip()]
        except Exception:
            pass
    # Fallback to comma/whitespace separated
    return [p.strip() for p in raw_str.replace("\n", ",").replace(";", ",").split(",") if p.strip()]


def _format_pincodes(pincodes: List[str]) -> str:
    """Normalize list of PIN codes as a clean JSON array string."""
    cleaned = []
    for p in pincodes:
        clean = clean_pincode(p)
        if clean and clean not in cleaned:
            cleaned.append(clean)
    return json.dumps(cleaned)


# ---------- Zone Management ----------

def create_delivery_zone(db: Session, payload: schemas.DeliveryZoneCreate) -> models.DeliveryZone:
    """Create a new delivery zone with designated serviceable PIN codes and thresholds."""
    existing = db.query(models.DeliveryZone).filter(models.DeliveryZone.name == payload.name.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery zone with name '{payload.name}' already exists",
        )

    pincodes_json = _format_pincodes(payload.serviceable_pincodes)
    zone = models.DeliveryZone(
        name=payload.name.strip(),
        state=payload.state.strip(),
        district=payload.district.strip(),
        city=payload.city.strip() if payload.city else None,
        serviceable_pincodes=pincodes_json,
        is_active=payload.is_active,
        min_batch_threshold_kg=payload.min_batch_threshold_kg,
        max_batch_weight_kg=payload.max_batch_weight_kg,
        max_batch_orders=payload.max_batch_orders,
        preparation_buffer_hours=payload.preparation_buffer_hours,
        dispatch_buffer_hours=payload.dispatch_buffer_hours,
        allows_home_delivery=payload.allows_home_delivery,
        allows_drop_point=payload.allows_drop_point,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


def update_delivery_zone(db: Session, zone_id: str, payload: schemas.DeliveryZoneUpdate) -> models.DeliveryZone:
    """Update delivery zone parameters and active status."""
    zone = db.query(models.DeliveryZone).filter(models.DeliveryZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery zone not found")

    if payload.name is not None:
        zone.name = payload.name.strip()
    if payload.state is not None:
        zone.state = payload.state.strip()
    if payload.district is not None:
        zone.district = payload.district.strip()
    if payload.city is not None:
        zone.city = payload.city.strip()
    if payload.serviceable_pincodes is not None:
        zone.serviceable_pincodes = _format_pincodes(payload.serviceable_pincodes)
    if payload.is_active is not None:
        zone.is_active = payload.is_active
    if payload.min_batch_threshold_kg is not None:
        zone.min_batch_threshold_kg = payload.min_batch_threshold_kg
    if payload.max_batch_weight_kg is not None:
        zone.max_batch_weight_kg = payload.max_batch_weight_kg
    if payload.max_batch_orders is not None:
        zone.max_batch_orders = payload.max_batch_orders
    if payload.preparation_buffer_hours is not None:
        zone.preparation_buffer_hours = payload.preparation_buffer_hours
    if payload.dispatch_buffer_hours is not None:
        zone.dispatch_buffer_hours = payload.dispatch_buffer_hours
    if payload.allows_home_delivery is not None:
        zone.allows_home_delivery = payload.allows_home_delivery
    if payload.allows_drop_point is not None:
        zone.allows_drop_point = payload.allows_drop_point

    db.commit()
    db.refresh(zone)
    return zone


def list_delivery_zones(db: Session, active_only: bool = False) -> List[models.DeliveryZone]:
    """Retrieve all delivery zones."""
    query = db.query(models.DeliveryZone)
    if active_only:
        query = query.filter(models.DeliveryZone.is_active == True)  # noqa: E712
    return query.order_by(models.DeliveryZone.name).all()


def get_delivery_zone(db: Session, zone_id: str) -> models.DeliveryZone:
    """Retrieve single delivery zone by ID."""
    zone = db.query(models.DeliveryZone).filter(models.DeliveryZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery zone not found")
    return zone


# ---------- Shared Drop Point Management ----------

def create_shared_drop_point(db: Session, payload: schemas.SharedDropPointCreate) -> models.SharedDropPoint:
    """Register a new shared drop point associated with a delivery zone."""
    zone = db.query(models.DeliveryZone).filter(models.DeliveryZone.id == payload.zone_id).first()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated delivery zone not found")

    pincode = clean_pincode(payload.pincode)
    if not pincode:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 6-digit Indian PIN code")

    drop_point = models.SharedDropPoint(
        zone_id=zone.id,
        name=payload.name.strip(),
        address_line=payload.address_line.strip(),
        locality=payload.locality.strip() if payload.locality else None,
        city=payload.city.strip(),
        district=payload.district.strip(),
        state=payload.state.strip(),
        pincode=pincode,
        operating_hours=payload.operating_hours.strip(),
        contact_phone=payload.contact_phone.strip() if payload.contact_phone else None,
        capacity_orders=payload.capacity_orders,
        is_active=payload.is_active,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(drop_point)
    db.commit()
    db.refresh(drop_point)
    return drop_point


def update_shared_drop_point(db: Session, drop_point_id: str, payload: schemas.SharedDropPointUpdate) -> models.SharedDropPoint:
    """Update drop point details."""
    dp = db.query(models.SharedDropPoint).filter(models.SharedDropPoint.id == drop_point_id).first()
    if not dp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared drop point not found")

    if payload.name is not None:
        dp.name = payload.name.strip()
    if payload.address_line is not None:
        dp.address_line = payload.address_line.strip()
    if payload.locality is not None:
        dp.locality = payload.locality.strip()
    if payload.operating_hours is not None:
        dp.operating_hours = payload.operating_hours.strip()
    if payload.contact_phone is not None:
        dp.contact_phone = payload.contact_phone.strip()
    if payload.capacity_orders is not None:
        dp.capacity_orders = payload.capacity_orders
    if payload.is_active is not None:
        dp.is_active = payload.is_active

    db.commit()
    db.refresh(dp)
    return dp


def list_shared_drop_points(db: Session, zone_id: Optional[str] = None, active_only: bool = True) -> List[models.SharedDropPoint]:
    """Retrieve shared drop points, optionally filtered by zone."""
    query = db.query(models.SharedDropPoint)
    if zone_id:
        query = query.filter(models.SharedDropPoint.zone_id == zone_id)
    if active_only:
        query = query.filter(models.SharedDropPoint.is_active == True)  # noqa: E712
    return query.order_by(models.SharedDropPoint.name).all()


def find_zone_for_pincode(db: Session, pincode: Optional[str]) -> Optional[models.DeliveryZone]:
    """Identify the active delivery zone covering the given PIN code."""
    if not pincode:
        return None
    cleaned = clean_pincode(pincode)
    if not cleaned:
        return None

    zones = db.query(models.DeliveryZone).filter(models.DeliveryZone.is_active == True).all()  # noqa: E712
    for z in zones:
        pincodes = _parse_pincodes(z.serviceable_pincodes)
        if cleaned in pincodes:
            return z
    return None


def evaluate_serviceability(
    db: Session,
    pincode: str,
    delivery_mode: Optional[str] = "home_delivery",
    order_weight_kg: Optional[float] = None,
) -> schemas.ServiceabilityCheckResponse:
    """
    Comprehensive Server-side Serviceability Evaluation:
      1. Validates 6-digit Indian PIN code format.
      2. Matches active DeliveryZone covering the PIN code.
      3. Verifies requested delivery mode support in that zone.
      4. Fetches active SharedDropPoints.
      5. Checks maximum payload weight constraint if specified.
    """
    cleaned_pincode = clean_pincode(pincode)
    if not cleaned_pincode:
        return schemas.ServiceabilityCheckResponse(
            serviceable=False,
            pincode=pincode,
            reasons=["Invalid Indian PIN code format. Must be a 6-digit number not starting with 0."],
        )

    zone = find_zone_for_pincode(db, cleaned_pincode)
    if not zone:
        return schemas.ServiceabilityCheckResponse(
            serviceable=False,
            pincode=cleaned_pincode,
            reasons=[f"PIN code {cleaned_pincode} is not currently covered by any active delivery zone."],
        )

    reasons: List[str] = []
    serviceable = True

    # Mode validation
    if delivery_mode == "home_delivery" and not zone.allows_home_delivery:
        serviceable = False
        reasons.append(f"Home delivery is currently disabled for zone '{zone.name}'.")

    if delivery_mode == "shared_drop_point" and not zone.allows_drop_point:
        serviceable = False
        reasons.append(f"Shared drop-point delivery is currently disabled for zone '{zone.name}'.")

    # Weight constraint
    if order_weight_kg and order_weight_kg > zone.max_batch_weight_kg:
        serviceable = False
        reasons.append(
            f"Order weight ({order_weight_kg} kg) exceeds maximum permissible batch capacity ({zone.max_batch_weight_kg} kg) for zone '{zone.name}'."
        )

    # Active drop points in zone
    active_drop_points = (
        db.query(models.SharedDropPoint)
        .filter(models.SharedDropPoint.zone_id == zone.id, models.SharedDropPoint.is_active == True)  # noqa: E712
        .all()
    )

    if delivery_mode == "shared_drop_point" and not active_drop_points:
        serviceable = False
        reasons.append(f"No active shared drop points are currently available in zone '{zone.name}'.")

    drop_point_outs = [schemas.SharedDropPointOut.model_validate(dp) for dp in active_drop_points]

    return schemas.ServiceabilityCheckResponse(
        serviceable=serviceable,
        pincode=cleaned_pincode,
        zone_id=zone.id,
        zone_name=zone.name,
        state=zone.state,
        district=zone.district,
        allows_home_delivery=zone.allows_home_delivery,
        allows_drop_point=zone.allows_drop_point,
        available_drop_points=drop_point_outs,
        available_slots=["morning", "afternoon", "evening"],
        reasons=reasons,
    )


# Aliases for backward and test compatibility
check_pincode_serviceability = evaluate_serviceability
list_active_zones = list_delivery_zones
list_active_drop_points = list_shared_drop_points

