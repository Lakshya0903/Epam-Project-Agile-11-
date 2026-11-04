"""
Logistics & Delivery Endpoints Router
Primary Maintainer: Hemant Yadav (Backend Developer 3)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.security import get_current_user, require_role
from ..services.payment_engine import confirm_delivery

router = APIRouter(tags=["logistics"])


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
    """DELIVERY CONFIRMATION (OTP) -> Triggers Automated PAYMENT SETTLEMENT."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return confirm_delivery(db, order, payload.otp)
