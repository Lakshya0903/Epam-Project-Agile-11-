"""
Smart Order Engine
Primary Maintainer: Lakshya Raj Malviya (Backend Lead)
Extended for Phase 2:
  - 5-State Canonical Order Lifecycle (PLACED -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED)
  - Role-based transition validation & immutable OrderStatusHistory
  - Server-side PIN code serviceability & Shared Drop Point validation
  - Cancellation with automatic inventory & batch capacity rollback
  - Order tracking with 24h dispute eligibility computation
"""

from typing import List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..utils.geo import clean_pincode
from .logistics_engine import assign_logistics_for_order
from .batch_engine import try_batch_individual_order
from .serviceability_engine import evaluate_serviceability, find_zone_for_pincode

# Valid state transition rules
VALID_TRANSITIONS = {
    # Phase 2 Canonical transitions
    models.OrderStatus.placed: [models.OrderStatus.confirmed, models.OrderStatus.matched, models.OrderStatus.batched, models.OrderStatus.cancelled],
    models.OrderStatus.confirmed: [models.OrderStatus.processing, models.OrderStatus.cancelled],
    models.OrderStatus.processing: [models.OrderStatus.shipped, models.OrderStatus.cancelled],
    models.OrderStatus.shipped: [models.OrderStatus.delivered],
    # Phase 1 Legacy transitions
    models.OrderStatus.matched: [models.OrderStatus.confirmed, models.OrderStatus.batched, models.OrderStatus.out_for_delivery, models.OrderStatus.shipped, models.OrderStatus.cancelled],
    models.OrderStatus.batched: [models.OrderStatus.confirmed, models.OrderStatus.out_for_delivery, models.OrderStatus.shipped, models.OrderStatus.cancelled],
    models.OrderStatus.out_for_delivery: [models.OrderStatus.delivered, models.OrderStatus.shipped],
    models.OrderStatus.delivered: [models.OrderStatus.paid],
    models.OrderStatus.paid: [],
    models.OrderStatus.cancelled: [],
}


def _normalize_status(val: Any) -> models.OrderStatus:
    """Normalize lowercase or uppercase status input to canonical OrderStatus."""
    if isinstance(val, models.OrderStatus):
        return val
    clean = (val.value if hasattr(val, "value") else str(val)).lower().strip()
    try:
        return models.OrderStatus(clean)
    except ValueError:
        for s in models.OrderStatus:
            if s.value.lower() == clean:
                return s
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown order status: '{val}'",
        )


def create_order(db: Session, buyer: models.BuyerProfile, payload: schemas.OrderCreate) -> models.Order:
    """
    Implements: PLACE ORDER -> SERVICEABILITY VALIDATION -> INVENTORY RESERVATION -> BATCH/LOGISTICS
    """
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item",
        )

    # 1. Clean & Validate Address / Serviceability
    pincode = clean_pincode(payload.pincode) or clean_pincode(buyer.pincode)
    mode = payload.delivery_mode.value if hasattr(payload.delivery_mode, "value") else str(payload.delivery_mode)

    zone = None
    if pincode:
        service_eval = evaluate_serviceability(db, pincode=pincode, delivery_mode=mode)
        if not service_eval.serviceable:
            reasons_text = "; ".join(service_eval.reasons) or "Location not serviceable"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Delivery is not serviceable for PIN {pincode}: {reasons_text}",
            )
        if service_eval.zone_id:
            zone = db.query(models.DeliveryZone).filter(models.DeliveryZone.id == service_eval.zone_id).first()

    # If shared drop point requested, verify drop point exists and is active
    drop_point = None
    if mode == "shared_drop_point":
        if not payload.drop_point_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid drop_point_id is required for shared drop-point delivery",
            )
        drop_point = db.query(models.SharedDropPoint).filter(models.SharedDropPoint.id == payload.drop_point_id).first()
        if not drop_point or not drop_point.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected shared drop point is invalid or inactive",
            )
        if zone and drop_point.zone_id != zone.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected drop point does not belong to the serviceable zone for this PIN code",
            )

    order = models.Order(
        buyer_id=buyer.id,
        order_type=payload.order_type,
        delivery_mode=mode,
        delivery_location=payload.delivery_location,
        address_line=payload.address_line,
        pincode=pincode,
        city=payload.city or (drop_point.city if drop_point else None),
        district=payload.district or (drop_point.district if drop_point else None),
        state=payload.state or (drop_point.state if drop_point else None),
        drop_point_id=drop_point.id if drop_point else None,
        zone_id=zone.id if zone else None,
        latitude=payload.latitude or (drop_point.latitude if drop_point else None),
        longitude=payload.longitude or (drop_point.longitude if drop_point else None),
        delivery_slot=payload.delivery_slot,
        status=models.OrderStatus.placed,
    )
    db.add(order)
    db.flush()

    total_amount = 0.0
    total_weight = 0.0
    order_items: List[models.OrderItem] = []

    for item in payload.items:
        produce = db.query(models.Produce).filter(models.Produce.id == item.produce_id).first()
        if not produce:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produce item {item.produce_id} not found",
            )
        if produce.status == models.ProduceStatus.sold_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{produce.product_name} is currently sold out",
            )
        if item.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero",
            )
        if produce.quantity_available < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {produce.quantity_available} {produce.unit} of {produce.product_name} available",
            )

        subtotal = round(item.quantity * produce.price_per_unit, 2)
        order_item = models.OrderItem(
            order_id=order.id,
            produce_id=produce.id,
            quantity=item.quantity,
            unit_price=produce.price_per_unit,
            subtotal=subtotal,
        )
        db.add(order_item)
        order_items.append(order_item)

        # Atomic inventory deduction
        produce.quantity_available -= item.quantity
        if produce.quantity_available <= 0:
            produce.quantity_available = 0.0
            produce.status = models.ProduceStatus.sold_out

        total_amount += subtotal
        total_weight += item.quantity

    order.total_amount = round(total_amount, 2)
    db.flush()

    # Initial order status history
    history = models.OrderStatusHistory(
        order_id=order.id,
        previous_status=None,
        new_status=models.OrderStatus.placed.value,
        actor_id=buyer.user_id,
        actor_role="buyer",
        reason="Order placed successfully",
    )
    db.add(history)

    # Branch according to order type
    if payload.order_type == models.OrderType.bulk:
        order.status = models.OrderStatus.confirmed
        order.confirmed_at = datetime.now(timezone.utc)
        assign_logistics_for_order(db, order, total_weight)
    else:
        # Individual order: smart batching
        try_batch_individual_order(db, order, total_weight)

    db.commit()
    db.refresh(order)
    return order


def transition_order_status(
    db: Session,
    order: Optional[models.Order] = None,
    target_status: str = "",
    actor: Optional[models.User] = None,
    reason: Optional[str] = None,
    order_id: Optional[str] = None,
    new_status: Optional[str] = None,
) -> models.Order:
    """
    Centralized State Transition Validation & Enforcement:
      PLACED -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED
    Enforces role permissions and maintains audit history.
    """
    if order is None and order_id:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    target = target_status or new_status or ""
    new_st = _normalize_status(target)
    curr_status = order.status

    if curr_status == new_status:
        return order  # Idempotent no-op

    # Check validity of transition
    valid_targets = VALID_TRANSITIONS.get(curr_status, [])
    # Also allow transition to canonical confirmed from legacy batched/matched
    if new_status not in valid_targets and not (
        actor.role == models.UserRole.admin
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order transition from '{curr_status.value}' to '{new_status.value}'",
        )

    # Role permission enforcement
    now_utc = datetime.now(timezone.utc)

    if new_status == models.OrderStatus.confirmed:
        if actor.role not in (models.UserRole.farmer, models.UserRole.admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only farmers or admins can confirm an order")
        order.confirmed_at = now_utc

    elif new_status == models.OrderStatus.processing:
        if actor.role not in (models.UserRole.farmer, models.UserRole.admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only farmers or admins can mark an order as processing")
        order.processing_at = now_utc

    elif new_status == models.OrderStatus.shipped:
        if actor.role not in (models.UserRole.logistics, models.UserRole.admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only logistics partners or admins can mark an order as shipped")
        order.shipped_at = now_utc

        # Ensure Delivery record exists and is in in_transit state
        delivery = db.query(models.Delivery).filter(models.Delivery.order_id == order.id).first()
        if not delivery:
            delivery = models.Delivery(
                order_id=order.id,
                delivery_mode=order.delivery_mode or "home_delivery",
                drop_point_id=order.drop_point_id,
                status=models.DeliveryStatus.in_transit,
            )
            db.add(delivery)
        else:
            delivery.status = models.DeliveryStatus.in_transit

    elif new_status == models.OrderStatus.delivered:
        # Delivered should be driven by receiver confirmation (Stage 4). Admins may override with reason.
        if actor.role != models.UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Delivery state must be confirmed by the authorized receiver via the delivery confirmation endpoint",
            )
        order.delivered_at = now_utc

    elif new_status == models.OrderStatus.cancelled:
        cancel_order(db, order, actor, reason=reason)
        return order

    # Record audit log
    history = models.OrderStatusHistory(
        order_id=order.id,
        previous_status=curr_status.value,
        new_status=new_status.value,
        actor_id=actor.id,
        actor_role=actor.role.value,
        reason=reason or f"Transitioned to {new_status.value}",
    )
    db.add(history)

    order.status = new_status
    db.commit()
    db.refresh(order)
    return order


def cancel_order(
    db: Session,
    order: Optional[models.Order] = None,
    actor: Optional[models.User] = None,
    reason: Optional[str] = None,
    order_id: Optional[str] = None,
) -> models.Order:
    """
    Cancels order, rolling back inventory and releasing batch capacity.
    """
    if order is None and order_id:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status in (models.OrderStatus.shipped, models.OrderStatus.delivered, models.OrderStatus.paid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in '{order.status.value}' state.",
        )

    # Roll back reserved inventory
    for item in order.items:
        if item.produce:
            item.produce.quantity_available += item.quantity
            if item.produce.status == models.ProduceStatus.sold_out and item.produce.quantity_available > 0:
                item.produce.status = models.ProduceStatus.available

    # Release batch capacity if assigned
    if order.batch_id:
        batch = db.query(models.DeliveryBatch).filter(models.DeliveryBatch.id == order.batch_id).first()
        if batch:
            order_weight = sum(i.quantity for i in order.items)
            batch.total_weight_kg -= order_weight
            if batch.total_weight_kg < 0:
                batch.total_weight_kg = 0.0
            if batch.current_order_count and batch.current_order_count > 0:
                batch.current_order_count -= 1
            if batch.status == "full":
                batch.status = "open"

    prev = order.status.value
    order.status = models.OrderStatus.cancelled

    history = models.OrderStatusHistory(
        order_id=order.id,
        previous_status=prev,
        new_status=models.OrderStatus.cancelled.value,
        actor_id=actor.id,
        actor_role=actor.role.value,
        reason=reason or "Order cancelled",
    )
    db.add(history)

    db.commit()
    db.refresh(order)
    return order


def get_order_tracking(db: Session, order: models.Order) -> schemas.OrderTrackingOut:
    """
    Synthesize complete order progress, delivery mode, drop point,
    history, and dispute eligibility.
    """
    now_utc = datetime.now(timezone.utc)
    is_dispute_eligible = False
    remaining_hours = None

    if order.delivered_at:
        del_time = order.delivered_at
        if del_time.tzinfo is None:
            del_time = del_time.replace(tzinfo=timezone.utc)
        elapsed = now_utc - del_time
        max_window = timedelta(hours=settings.dispute_window_hours)
        if elapsed <= max_window and not order.dispute:
            is_dispute_eligible = True
            remaining_hours = round(max(0.0, (max_window - elapsed).total_seconds() / 3600.0), 1)

    receiver_pending = (
        order.status in (models.OrderStatus.shipped, models.OrderStatus.out_for_delivery)
        and (not order.delivery or not order.delivery.receiver_confirmed)
    )

    batch_out = schemas.DeliveryBatchOut.model_validate(order.batch) if order.batch else None
    drop_point_out = schemas.SharedDropPointOut.model_validate(order.drop_point) if order.drop_point else None
    history_outs = [schemas.OrderStatusHistoryOut.model_validate(h) for h in order.status_history]

    return schemas.OrderTrackingOut(
        order_id=order.id,
        current_status=order.status,
        delivery_mode=order.delivery_mode or "home_delivery",
        delivery_slot=order.delivery_slot,
        delivery_location=order.delivery_location,
        pincode=order.pincode,
        drop_point=drop_point_out,
        batch=batch_out,
        status_history=history_outs,
        receiver_confirmation_pending=receiver_pending,
        dispute_eligible=is_dispute_eligible,
        dispute_remaining_hours=remaining_hours,
    )
