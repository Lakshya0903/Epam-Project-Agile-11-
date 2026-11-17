"""
Orders Router
Primary Maintainer: Hemant Yadav & Lakshya Raj Malviya
Extended for Phase 2:
  - 5-State Lifecycle Tracking & Transition Endpoints
  - Order Tracking API with 24h Dispute Eligibility
  - Farmer Incoming Orders Visibility
  - Safe Order Cancellation with Inventory/Capacity Rollback
"""

from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..database import get_db
from ..utils.security import get_current_user, require_role
from ..services.order_engine import (
    create_order,
    transition_order_status,
    cancel_order,
    get_order_tracking,
)
from ..services.batch_engine import request_direct_delivery

router = APIRouter(prefix="/orders", tags=["orders"])


def _buyer_profile(db: Session, user: models.User) -> models.BuyerProfile:
    """Helper to verify and retrieve the BuyerProfile for current user."""
    profile = db.query(models.BuyerProfile).filter(models.BuyerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Buyer profile not found for this account",
        )
    return profile


def _farmer_profile(db: Session, user: models.User) -> models.FarmerProfile:
    """Helper to verify and retrieve the FarmerProfile for current user."""
    profile = db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Farmer profile not found for this account",
        )
    return profile


def _format_order_out(order: models.Order) -> schemas.OrderOut:
    """Helper to calculate dispute eligibility and populate schemas.OrderOut."""
    now_utc = datetime.now(timezone.utc)
    is_eligible = False
    if order.delivered_at:
        del_time = order.delivered_at
        if del_time.tzinfo is None:
            del_time = del_time.replace(tzinfo=timezone.utc)
        if (now_utc - del_time) <= timedelta(hours=settings.dispute_window_hours) and not order.dispute:
            is_eligible = True

    out = schemas.OrderOut.model_validate(order)
    out.is_dispute_eligible = is_eligible
    return out


@router.post("", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def place_order(
    payload: schemas.OrderCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.buyer)),
):
    """PLACE ORDER -> SAVE IN DATABASE -> SMART ORDER ENGINE."""
    buyer = _buyer_profile(db, user)

    expected_type = (
        models.OrderType.bulk if buyer.buyer_type == models.BuyerType.bulk else models.OrderType.individual
    )
    if payload.order_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your account is registered as a {buyer.buyer_type.value} buyer; order_type must be '{expected_type.value}'",
        )

    order = create_order(db, buyer, payload)
    return _format_order_out(order)


@router.get("/mine", response_model=List[schemas.OrderOut])
def my_orders(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.buyer)),
):
    """Retrieve all orders placed by the currently authenticated buyer."""
    buyer = _buyer_profile(db, user)
    orders = (
        db.query(models.Order)
        .filter(models.Order.buyer_id == buyer.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )
    return [_format_order_out(o) for o in orders]


@router.get("/farmer", response_model=List[schemas.OrderOut])
def farmer_orders(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.farmer, models.UserRole.admin)),
):
    """Retrieve incoming orders containing produce supplied by the authenticated farmer."""
    farmer = _farmer_profile(db, user) if user.role == models.UserRole.farmer else None
    query = (
        db.query(models.Order)
        .join(models.OrderItem, models.OrderItem.order_id == models.Order.id)
        .join(models.Produce, models.Produce.id == models.OrderItem.produce_id)
    )
    if farmer:
        query = query.filter(models.Produce.farmer_id == farmer.id)
    orders = query.distinct().order_by(models.Order.created_at.desc()).all()
    return [_format_order_out(o) for o in orders]


@router.get("/logistics", response_model=List[schemas.OrderOut])
def logistics_orders(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.logistics, models.UserRole.admin)),
):
    """Return orders that currently have a delivery record assigned."""
    orders = (
        db.query(models.Order)
        .join(models.Delivery, models.Delivery.order_id == models.Order.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )
    return [_format_order_out(o) for o in orders]


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Fetch an order by its unique ID."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return _format_order_out(order)


@router.get("/{order_id}/tracking", response_model=schemas.OrderTrackingOut)
def get_order_tracking_endpoint(
    order_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Retrieve complete 5-state lifecycle progress, history, and dispute eligibility."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return get_order_tracking(db, order)


@router.patch("/{order_id}/status", response_model=schemas.OrderOut)
def update_order_status(
    order_id: str,
    payload: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Transition order status through canonical lifecycle with role verification."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    updated = transition_order_status(db, order, payload.status.value, actor=user, reason=payload.reason)
    return _format_order_out(updated)


@router.post("/{order_id}/cancel", response_model=schemas.OrderOut)
def cancel_order_endpoint(
    order_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Cancel order, rollback reserved stock and release batch capacity."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    cancelled = cancel_order(db, order, actor=user, reason="Cancelled by user")
    return _format_order_out(cancelled)


@router.post("/{order_id}/request-direct-delivery", response_model=schemas.OrderOut)
def choose_direct_delivery(
    order_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.buyer)),
):
    """Customer Options -> Direct Delivery (Pay Extra Cost) for an order waiting in a batch."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if order.status not in (models.OrderStatus.batched, models.OrderStatus.placed, models.OrderStatus.matched):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not currently waiting in a batch",
        )

    updated = request_direct_delivery(db, order)
    return _format_order_out(updated)
