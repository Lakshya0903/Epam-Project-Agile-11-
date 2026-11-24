"""
Logistics & Delivery Endpoints Router
Primary Maintainer: Hemant Yadav (Backend Developer 3)
Extended for Phase 2: Delivery Zones, Shared Drop Points, Serviceability Checks,
Delivery Batches Inspection, and Receiver Confirmation (Without OTP).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.security import get_current_user, require_role
from ..services.payment_engine import confirm_delivery, confirm_receiver_receipt
from ..services.serviceability_engine import (
    create_delivery_zone,
    update_delivery_zone,
    list_delivery_zones,
    get_delivery_zone,
    create_shared_drop_point,
    update_shared_drop_point,
    list_shared_drop_points,
    evaluate_serviceability,
)

router = APIRouter(tags=["logistics"])


# ---------- Phase 2: Serviceability & Zones ----------

@router.get("/logistics/serviceability", response_model=schemas.ServiceabilityCheckResponse)
def check_serviceability_get(
    pincode: str,
    delivery_mode: Optional[str] = "home_delivery",
    order_weight_kg: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Evaluate nationwide delivery serviceability for an Indian PIN code via GET."""
    return evaluate_serviceability(
        db=db,
        pincode=pincode,
        delivery_mode=delivery_mode,
        order_weight_kg=order_weight_kg,
    )


@router.post("/logistics/serviceability", response_model=schemas.ServiceabilityCheckResponse)
def check_serviceability_post(
    payload: schemas.ServiceabilityCheckRequest,
    db: Session = Depends(get_db),
):
    """Evaluate nationwide delivery serviceability for an Indian PIN code via POST."""
    mode = payload.delivery_mode.value if hasattr(payload.delivery_mode, "value") else str(payload.delivery_mode)
    return evaluate_serviceability(
        db=db,
        pincode=payload.pincode,
        delivery_mode=mode,
        order_weight_kg=payload.order_weight_kg,
    )


@router.post("/logistics/zones", response_model=schemas.DeliveryZoneOut, status_code=status.HTTP_201_CREATED)
def add_zone(
    payload: schemas.DeliveryZoneCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin)),
):
    """Create a new delivery zone with designated serviceable PIN codes and thresholds (Admin only)."""
    return create_delivery_zone(db, payload)


@router.get("/logistics/zones", response_model=List[schemas.DeliveryZoneOut])
def get_zones(
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    """List all delivery zones."""
    return list_delivery_zones(db, active_only=active_only)


@router.get("/logistics/zones/{zone_id}", response_model=schemas.DeliveryZoneOut)
def get_zone(zone_id: str, db: Session = Depends(get_db)):
    """Fetch single delivery zone details."""
    return get_delivery_zone(db, zone_id)


@router.patch("/logistics/zones/{zone_id}", response_model=schemas.DeliveryZoneOut)
def patch_zone(
    zone_id: str,
    payload: schemas.DeliveryZoneUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin)),
):
    """Update delivery zone settings, capacities, and active status (Admin only)."""
    return update_delivery_zone(db, zone_id, payload)


# ---------- Phase 2: Shared Drop Points ----------

@router.post("/logistics/drop-points", response_model=schemas.SharedDropPointOut, status_code=status.HTTP_201_CREATED)
def add_drop_point(
    payload: schemas.SharedDropPointCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin)),
):
    """Create a new shared drop point for cluster deliveries (Admin only)."""
    return create_shared_drop_point(db, payload)


@router.get("/logistics/drop-points", response_model=List[schemas.SharedDropPointOut])
def get_drop_points(
    zone_id: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """List shared drop points, optionally filtered by zone."""
    return list_shared_drop_points(db, zone_id=zone_id, active_only=active_only)


@router.patch("/logistics/drop-points/{drop_point_id}", response_model=schemas.SharedDropPointOut)
def patch_drop_point(
    drop_point_id: str,
    payload: schemas.SharedDropPointUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin)),
):
    """Update shared drop point attributes (Admin only)."""
    return update_shared_drop_point(db, drop_point_id, payload)


# ---------- Phase 2: Delivery Batches ----------

@router.get("/logistics/batches", response_model=List[schemas.DeliveryBatchOut])
def list_batches(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin, models.UserRole.logistics)),
):
    """Inspect all active or closed delivery batches."""
    query = db.query(models.DeliveryBatch)
    if status_filter:
        query = query.filter(models.DeliveryBatch.status == status_filter)
    return query.order_by(models.DeliveryBatch.created_at.desc()).all()


@router.get("/logistics/batches/{batch_id}", response_model=schemas.DeliveryBatchOut)
def get_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Fetch details of a specific delivery batch."""
    batch = db.query(models.DeliveryBatch).filter(models.DeliveryBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery batch not found")
    return batch


@router.post("/logistics/batches/{batch_id}/close", response_model=schemas.DeliveryBatchOut)
def close_batch_manually(
    batch_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin)),
):
    """Manually close an open batch to prevent further assignments (Admin only)."""
    batch = db.query(models.DeliveryBatch).filter(models.DeliveryBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery batch not found")
    batch.status = "full"
    db.commit()
    db.refresh(batch)
    return batch


# ---------- Phase 2: Receiver Delivery Confirmation (NO OTP) ----------

@router.post("/logistics/deliveries/{delivery_id}/confirm-receipt", response_model=schemas.DeliveryOut)
def receiver_confirm_receipt(
    delivery_id: str,
    payload: Optional[schemas.ReceiverReceiptConfirm] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """
    RECEIVER DELIVERY CONFIRMATION (Without OTP):
      Allows the authenticated buyer/receiver or admin to confirm receipt of the delivery.
      Records receiver identity and initiates the 24-hour buyer confirmation & dispute window.
    """
    notes = payload.notes if payload else None
    return confirm_receiver_receipt(db, delivery_id=delivery_id, actor=user, notes=notes)


# ---------- Phase 1: Existing Endpoints (Preserved for Backward Compatibility) ----------

@router.post("/logistics-partners", response_model=schemas.LogisticsPartnerOut, status_code=status.HTTP_201_CREATED)
def register_partner(
    payload: schemas.LogisticsPartnerCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin, models.UserRole.logistics)),
):
    """Register a new vehicle partner in the logistics pool."""
    partner = models.LogisticsPartner(**payload.model_dump())
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.get("/logistics-partners", response_model=List[schemas.LogisticsPartnerOut])
def list_partners(db: Session = Depends(get_db)):
    """List all registered logistics fleet partners."""
    return db.query(models.LogisticsPartner).all()


@router.get("/orders/{order_id}/delivery", response_model=schemas.DeliveryOut)
def get_delivery(
    order_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Retrieve the delivery dispatch record for an order."""
    delivery = db.query(models.Delivery).filter(models.Delivery.order_id == order_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No delivery record found yet for this order",
        )
    return delivery


@router.post("/orders/{order_id}/confirm-delivery", response_model=schemas.DeliveryOut)
def confirm_delivery_endpoint(
    order_id: str,
    payload: schemas.DeliveryConfirm,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """LEGACY DELIVERY CONFIRMATION (OTP) -> Retained for Phase 1 compatibility."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return confirm_delivery(db, order, payload.otp)
