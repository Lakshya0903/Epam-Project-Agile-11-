"""
Orders Router
Primary Maintainer: Hemant Yadav (Backend Developer 3)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.security import get_current_user, require_role
from ..services.order_engine import create_order
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

    return create_order(db, buyer, payload)


@router.get("/mine", response_model=List[schemas.OrderOut])
def my_orders(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.buyer)),
):
    """Retrieve all orders placed by the currently authenticated buyer."""
    buyer = _buyer_profile(db, user)
    return (
        db.query(models.Order)
        .filter(models.Order.buyer_id == buyer.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )


@router.get("/logistics", response_model=List[schemas.OrderOut])
def logistics_orders(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.logistics, models.UserRole.admin)),
):
    """Return orders that currently have a delivery record assigned."""
    return (
        db.query(models.Order)
        .join(models.Delivery, models.Delivery.order_id == models.Order.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )


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
    return order


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
    if order.status != models.OrderStatus.batched:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not currently waiting in a batch",
        )

    return request_direct_delivery(db, order)
