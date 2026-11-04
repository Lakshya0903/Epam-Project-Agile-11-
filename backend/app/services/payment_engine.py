"""
Payment Engine: OTP Verification & 3-Way Settlement Ledger
Primary Maintainer: Hemant Yadav (Backend Developer 3)
"""

from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import models
from ..config import settings


def confirm_delivery(db: Session, order: models.Order, otp: str) -> models.Delivery:
    """
    DELIVERY CONFIRMATION (OTP):
      1. Validates OTP against delivery record
      2. Marks delivery as delivered
      3. Updates order status to delivered
      4. Triggers atomic payment settlement
    """
    delivery = order.delivery
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No delivery record found for this order",
        )
    if delivery.status == models.DeliveryStatus.delivered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery has already been confirmed for this order",
        )
    if delivery.otp != otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP provided",
        )

    delivery.status = models.DeliveryStatus.delivered
    delivery.delivered_at = datetime.now(timezone.utc)
    order.status = models.OrderStatus.delivered
    db.flush()

    settle_payment(db, order)

    db.commit()
    db.refresh(delivery)
    return delivery


def settle_payment(db: Session, order: models.Order) -> models.Payment:
    """
    PAYMENT SETTLEMENT:
      Splits total order amount into:
        - Farmer share: Gross produce value minus platform fee percentage
        - Logistics share: Agreed freight delivery cost
        - Platform revenue: Platform produce fee + logistics markup
    """
    delivery = order.delivery
    logistics_cost = delivery.delivery_cost or 0.0 if delivery else 0.0

    platform_fee_from_produce = round(order.total_amount * settings.platform_fee_percent / 100.0, 2)
    logistics_markup = round(logistics_cost * settings.logistics_share_percent / 100.0, 2)

    farmer_share = round(order.total_amount - platform_fee_from_produce, 2)
    logistics_share = round(logistics_cost, 2)
    platform_fee = round(platform_fee_from_produce + logistics_markup, 2)

    payment = db.query(models.Payment).filter(models.Payment.order_id == order.id).first()
    if not payment:
        payment = models.Payment(order_id=order.id)
        db.add(payment)

    payment.total_amount = order.total_amount
    payment.platform_fee = platform_fee
    payment.logistics_share = logistics_share
    payment.farmer_share = farmer_share
    payment.status = "settled"
    payment.settled_at = datetime.now(timezone.utc)

    order.status = models.OrderStatus.paid
    db.flush()
    return payment
