"""
Payments & Platform Revenue Router
Primary Maintainer: Hemant Yadav (Backend Developer 3)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.security import get_current_user, require_role

router = APIRouter(tags=["payments"])


@router.get("/orders/{order_id}/payment", response_model=schemas.PaymentOut)
def get_payment(
    order_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Retrieve settlement payment record for an order."""
    payment = db.query(models.Payment).filter(models.Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment has not been settled yet for this order",
        )
    return payment


@router.get("/platform/revenue")
def platform_revenue(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin)),
):
    """PLATFORM REVENUE DASHBOARD: Total revenue collected across settled payments."""
    totals = db.query(
        func.coalesce(func.sum(models.Payment.platform_fee), 0.0),
        func.coalesce(func.sum(models.Payment.farmer_share), 0.0),
        func.coalesce(func.sum(models.Payment.logistics_share), 0.0),
        func.count(models.Payment.id),
    ).filter(models.Payment.status == "settled").first()

    platform_revenue_total, farmer_paid_total, logistics_paid_total, settled_count = totals
    return {
        "settled_orders": settled_count,
        "platform_revenue": round(float(platform_revenue_total), 2),
        "total_paid_to_farmers": round(float(farmer_paid_total), 2),
        "total_paid_to_logistics": round(float(logistics_paid_total), 2),
    }
