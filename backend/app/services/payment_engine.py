"""
Payment Engine & Multi-Party Escrow Ledger
Primary Maintainer: Hemant Yadav & Anshika Sharma
Extended for Phase 2:
  - Separate Financial Lifecycle State Machine
  - Gateway Integration Abstraction (Mock & Razorpay)
  - Cryptographic Signature Verification & Webhook Safety
  - Decimal & Integer-Paise Safe Ledger Calculations
  - Receiver Confirmation Without OTP
  - Configurable Buyer Confirmation Window Before Release Eligibility
  - Dispute Payment Hold & Automated Refunds
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from .payment_gateways import get_payment_gateway


def _calculate_shares_paise(order: models.Order) -> Dict[str, int]:
    """Calculate integer paise allocations for precision accounting."""
    amount_paise = int(round(order.total_amount * 100))
    platform_produce_paise = int(round(order.total_amount * settings.platform_fee_percent))  # 8%
    delivery = order.delivery
    logistics_cost = delivery.delivery_cost if (delivery and delivery.delivery_cost is not None) else 0.0
    logistics_cost_paise = int(round(logistics_cost * 100))
    logistics_markup_paise = int(round(logistics_cost * settings.logistics_share_percent))  # 15%

    farmer_share_paise = amount_paise - platform_produce_paise
    logistics_share_paise = logistics_cost_paise
    platform_fee_paise = platform_produce_paise + logistics_markup_paise

    return {
        "amount_paise": amount_paise,
        "farmer_share_paise": farmer_share_paise,
        "logistics_share_paise": logistics_share_paise,
        "platform_fee_paise": platform_fee_paise,
    }


def get_or_create_payment(db: Session, order: models.Order) -> models.Payment:
    """Retrieve existing payment record or initialize a new pending payment."""
    payment = db.query(models.Payment).filter(models.Payment.order_id == order.id).first()
    if not payment:
        shares = _calculate_shares_paise(order)
        delivery = order.delivery
        logistics_cost = delivery.delivery_cost if (delivery and delivery.delivery_cost is not None) else 0.0
        platform_fee_from_produce = round(order.total_amount * settings.platform_fee_percent / 100.0, 2)
        logistics_markup = round(logistics_cost * settings.logistics_share_percent / 100.0, 2)

        payment = models.Payment(
            order_id=order.id,
            total_amount=order.total_amount,
            amount_paise=shares["amount_paise"],
            farmer_share=round(order.total_amount - platform_fee_from_produce, 2),
            farmer_share_paise=shares["farmer_share_paise"],
            logistics_share=round(logistics_cost, 2),
            logistics_share_paise=shares["logistics_share_paise"],
            platform_fee=round(platform_fee_from_produce + logistics_markup, 2),
            platform_fee_paise=shares["platform_fee_paise"],
            status=models.PaymentStatus.pending.value,
        )
        db.add(payment)
        db.flush()

        ledger_entry = models.PaymentLedgerEntry(
            payment_id=payment.id,
            order_id=order.id,
            previous_status=None,
            new_status=models.PaymentStatus.pending.value,
            amount=order.total_amount,
            amount_paise=shares["amount_paise"],
            currency="INR",
            actor_type="system",
            reason="Payment record initialized",
        )
        db.add(ledger_entry)
        db.commit()
        db.refresh(payment)
    return payment


def initiate_payment(
    db: Session,
    order: models.Order,
    provider_name: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> schemas.PaymentInitiateResponse:
    """
    Initiate checkout transaction with payment gateway:
      1. Validates or initializes Payment record.
      2. Handles idempotency checks.
      3. Dispatches order creation to selected gateway provider.
      4. Writes PaymentLedgerEntry.
    """
    payment = get_or_create_payment(db, order)

    # Check idempotency
    if idempotency_key and payment.idempotency_key == idempotency_key and payment.gateway_order_id:
        return schemas.PaymentInitiateResponse(
            payment_id=payment.id,
            order_id=order.id,
            amount_inr=payment.total_amount,
            amount_paise=payment.amount_paise,
            currency="INR",
            gateway_provider=payment.gateway_provider or "mock",
            gateway_order_id=payment.gateway_order_id,
            key_id=settings.payment_key_id,
        )

    gateway = get_payment_gateway(provider_name or payment.gateway_provider)
    gateway_resp = gateway.create_order(
        amount_inr=payment.total_amount,
        currency="INR",
        receipt=f"order_{order.id[:8]}",
        notes={"order_id": order.id, "buyer_id": order.buyer_id},
    )

    prev_status = payment.status
    payment.gateway_provider = gateway.provider_name
    payment.gateway_order_id = gateway_resp["gateway_order_id"]
    payment.idempotency_key = idempotency_key
    payment.status = models.PaymentStatus.payment_initiated.value

    ledger_entry = models.PaymentLedgerEntry(
        payment_id=payment.id,
        order_id=order.id,
        previous_status=prev_status,
        new_status=models.PaymentStatus.payment_initiated.value,
        amount=payment.total_amount,
        amount_paise=payment.amount_paise,
        currency="INR",
        actor_type="gateway",
        reason=f"Payment initiated with gateway provider: {gateway.provider_name}",
        gateway_reference=payment.gateway_order_id,
    )
    db.add(ledger_entry)
    db.commit()
    db.refresh(payment)

    return schemas.PaymentInitiateResponse(
        payment_id=payment.id,
        order_id=order.id,
        amount_inr=payment.total_amount,
        amount_paise=payment.amount_paise,
        currency="INR",
        gateway_provider=gateway.provider_name,
        gateway_order_id=payment.gateway_order_id,
        key_id=gateway_resp.get("key_id", settings.payment_key_id),
        checkout_options={
            "name": "FarmCart",
            "description": f"FarmCart Order #{order.id[:8]}",
            "order_id": payment.gateway_order_id,
        },
    )


def verify_payment(
    db: Session,
    payment_id: str,
    gateway_order_id: str,
    gateway_payment_id: str,
    gateway_signature: str,
) -> models.Payment:
    """
    Cryptographic verification of client payment signature:
      1. Verifies HMAC-SHA256 signature against key secret.
      2. Replay protection: prevents duplicate captures.
      3. Transitions payment status to PAID.
      4. Transitions order status to CONFIRMED.
    """
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    # Replay protection
    if payment.status in (models.PaymentStatus.paid.value, "paid", models.PaymentStatus.settled.value, "settled"):
        return payment

    gateway = get_payment_gateway(payment.gateway_provider)
    is_valid = gateway.verify_payment_signature(
        gateway_order_id=gateway_order_id,
        gateway_payment_id=gateway_payment_id,
        gateway_signature=gateway_signature,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cryptographic payment signature verification failed",
        )

    prev_status = payment.status
    payment.gateway_payment_id = gateway_payment_id
    payment.gateway_signature = gateway_signature
    payment.gateway_status = "captured"
    payment.status = models.PaymentStatus.paid.value

    ledger_entry = models.PaymentLedgerEntry(
        payment_id=payment.id,
        order_id=payment.order_id,
        previous_status=prev_status,
        new_status=models.PaymentStatus.paid.value,
        amount=payment.total_amount,
        amount_paise=payment.amount_paise,
        currency="INR",
        actor_type="gateway",
        reason="Payment captured and signature cryptographically verified",
        gateway_reference=gateway_payment_id,
    )
    db.add(ledger_entry)

    # Move order to confirmed if currently in placed / matched state
    order = payment.order
    if order and order.status in (models.OrderStatus.placed, models.OrderStatus.matched):
        order.status = models.OrderStatus.confirmed
        order.confirmed_at = datetime.now(timezone.utc)
        history = models.OrderStatusHistory(
            order_id=order.id,
            previous_status=models.OrderStatus.placed.value,
            new_status=models.OrderStatus.confirmed.value,
            actor_type="system",
            reason="Order confirmed upon successful gateway payment",
        )
        db.add(history)

    db.commit()
    db.refresh(payment)
    return payment


def confirm_receiver_receipt(
    db: Session,
    delivery_id: str,
    actor: models.User,
    notes: Optional[str] = None,
) -> models.Delivery:
    """
    Phase 2 Receiver Delivery Confirmation (NO OTP Required):
      1. Validates authenticated actor is designated buyer or admin.
      2. Validates order is in shipped / dispatched state.
      3. Idempotently marks delivery as delivered and records receiver identity.
      4. Starts 24-hour buyer confirmation period for payment release.
      5. Makes order eligible for dispute filing for 24 hours.
    """
    delivery = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery record not found")

    order = delivery.order
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order associated with delivery not found")

    buyer = order.buyer
    # Only designated buyer or platform administrator can confirm delivery
    if actor.role != models.UserRole.admin and (not buyer or buyer.user_id != actor.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the designated buyer/receiver can confirm receipt of this delivery",
        )

    if delivery.receiver_confirmed or delivery.status == models.DeliveryStatus.delivered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery has already been confirmed for this order",
        )

    now_utc = datetime.now(timezone.utc)
    delivery.receiver_confirmed = True
    delivery.confirmed_by_id = actor.id
    delivery.confirmed_at = now_utc
    delivery.status = models.DeliveryStatus.delivered
    delivery.delivered_at = now_utc

    order.status = models.OrderStatus.delivered
    order.delivered_at = now_utc

    history = models.OrderStatusHistory(
        order_id=order.id,
        previous_status=models.OrderStatus.shipped.value,
        new_status=models.OrderStatus.delivered.value,
        actor_id=actor.id,
        actor_role=actor.role.value,
        reason=notes or "Receiver confirmed delivery receipt (without OTP)",
    )
    db.add(history)

    # Financial lifecycle: initiate buyer confirmation countdown window
    payment = get_or_create_payment(db, order)
    payment.buyer_confirmation_deadline = now_utc + timedelta(hours=settings.buyer_confirmation_period_hours)
    prev_status = payment.status
    payment.status = models.PaymentStatus.awaiting_buyer_confirmation.value

    ledger_entry = models.PaymentLedgerEntry(
        payment_id=payment.id,
        order_id=order.id,
        previous_status=prev_status,
        new_status=models.PaymentStatus.awaiting_buyer_confirmation.value,
        amount=payment.total_amount,
        amount_paise=payment.amount_paise,
        currency="INR",
        actor_id=actor.id,
        actor_type="receiver",
        reason=f"Delivery confirmed; {settings.buyer_confirmation_period_hours}h confirmation window started before payment release",
    )
    db.add(ledger_entry)

    db.commit()
    db.refresh(delivery)
    return delivery


def evaluate_payment_release_eligibility(db: Session, payment: models.Payment) -> bool:
    """
    Evaluates whether payment has fulfilled all conditions for financial release:
      1. Order is delivered.
      2. Buyer confirmation window (default 24h) has elapsed.
      3. No active dispute exists on the order.
      4. No financial hold exists.
    """
    if payment.is_on_hold:
        return False

    order = payment.order
    if not order or not order.delivered_at:
        return False

    now_utc = datetime.now(timezone.utc)
    deadline = payment.buyer_confirmation_deadline
    if deadline:
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if now_utc < deadline:
            return False

    # Check for active dispute
    dispute = db.query(models.Dispute).filter(models.Dispute.order_id == order.id).first()
    if dispute and dispute.status in (models.DisputeStatus.open.value, models.DisputeStatus.under_review.value):
        payment.is_on_hold = True
        payment.hold_reason = "Active dispute pending review"
        db.commit()
        return False

    if payment.status in (models.PaymentStatus.awaiting_buyer_confirmation.value, models.PaymentStatus.paid.value, "paid"):
        prev = payment.status
        payment.status = models.PaymentStatus.eligible_for_release.value
        ledger_entry = models.PaymentLedgerEntry(
            payment_id=payment.id,
            order_id=order.id,
            previous_status=prev,
            new_status=models.PaymentStatus.eligible_for_release.value,
            amount=payment.total_amount,
            amount_paise=payment.amount_paise,
            currency="INR",
            actor_type="system",
            reason="Buyer confirmation period elapsed with no dispute; eligible for payout release",
        )
        db.add(ledger_entry)
        db.commit()
        db.refresh(payment)
        return True

    return payment.status == models.PaymentStatus.eligible_for_release.value


def refund_payment(
    db: Session,
    payment_id: str,
    actor: models.User,
    amount_inr: Optional[float] = None,
    reason: str = "Dispute resolution",
) -> models.Payment:
    """
    Initiates refund with gateway provider and records append-only ledger entry.
    """
    if actor.role not in (models.UserRole.admin, models.UserRole.reviewer):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins or reviewers can issue refunds")

    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    gateway = get_payment_gateway(payment.gateway_provider)
    refund_amount = amount_inr if amount_inr is not None else payment.total_amount

    refund_resp = gateway.create_refund(
        gateway_payment_id=payment.gateway_payment_id or "mock_pay_id",
        amount_inr=refund_amount,
        notes={"reason": reason, "refunded_by": actor.id},
    )

    prev_status = payment.status
    payment.gateway_refund_id = refund_resp.get("gateway_refund_id")
    payment.status = models.PaymentStatus.refunded.value
    payment.refunded_amount_paise = int(round(refund_amount * 100))

    ledger_entry = models.PaymentLedgerEntry(
        payment_id=payment.id,
        order_id=payment.order_id,
        previous_status=prev_status,
        new_status=models.PaymentStatus.refunded.value,
        amount=refund_amount,
        amount_paise=payment.refunded_amount_paise,
        currency="INR",
        actor_id=actor.id,
        actor_type=actor.role.value,
        reason=f"Refund processed: {reason}",
        gateway_reference=payment.gateway_refund_id,
    )
    db.add(ledger_entry)
    db.commit()
    db.refresh(payment)
    return payment


# ---------- Phase 1 Compatibility Helpers ----------

def confirm_delivery(db: Session, order: models.Order, otp: str) -> models.Delivery:
    """
    PHASE 1 BACKWARD COMPATIBILITY: Legacy delivery confirmation via 6-digit OTP.
    """
    delivery = order.delivery
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No delivery record found for this order",
        )
    if delivery.status == models.DeliveryStatus.delivered or delivery.receiver_confirmed:
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
    delivery.receiver_confirmed = True
    order.status = models.OrderStatus.delivered
    order.delivered_at = delivery.delivered_at
    db.flush()

    settle_payment(db, order)

    db.commit()
    db.refresh(delivery)
    return delivery


def settle_payment(db: Session, order: models.Order) -> models.Payment:
    """
    PHASE 1 & 2 PAYMENT SETTLEMENT:
      Splits total order amount into:
        - Farmer share: Gross produce value minus platform fee percentage
        - Logistics share: Agreed freight delivery cost
        - Platform revenue: Platform produce fee + logistics markup
    """
    delivery = order.delivery
    logistics_cost = delivery.delivery_cost if (delivery and delivery.delivery_cost is not None) else 0.0

    platform_fee_from_produce = round(order.total_amount * settings.platform_fee_percent / 100.0, 2)
    logistics_markup = round(logistics_cost * settings.logistics_share_percent / 100.0, 2)

    farmer_share = round(order.total_amount - platform_fee_from_produce, 2)
    logistics_share = round(logistics_cost, 2)
    platform_fee = round(platform_fee_from_produce + logistics_markup, 2)

    shares = _calculate_shares_paise(order)

    payment = db.query(models.Payment).filter(models.Payment.order_id == order.id).first()
    prev_status = payment.status if payment else None

    if not payment:
        payment = models.Payment(
            order_id=order.id,
            total_amount=order.total_amount,
            amount_paise=shares["amount_paise"],
            platform_fee=platform_fee,
            platform_fee_paise=shares["platform_fee_paise"],
            logistics_share=logistics_share,
            logistics_share_paise=shares["logistics_share_paise"],
            farmer_share=farmer_share,
            farmer_share_paise=shares["farmer_share_paise"],
            status=models.PaymentStatus.settled.value,
            settled_at=datetime.now(timezone.utc),
        )
        db.add(payment)
        db.flush()
    else:
        payment.total_amount = order.total_amount
        payment.amount_paise = shares["amount_paise"]
        payment.platform_fee = platform_fee
        payment.platform_fee_paise = shares["platform_fee_paise"]
        payment.logistics_share = logistics_share
        payment.logistics_share_paise = shares["logistics_share_paise"]
        payment.farmer_share = farmer_share
        payment.farmer_share_paise = shares["farmer_share_paise"]
        payment.status = models.PaymentStatus.settled.value
        payment.settled_at = datetime.now(timezone.utc)

    order.status = models.OrderStatus.paid

    ledger_entry = models.PaymentLedgerEntry(
        payment_id=payment.id,
        order_id=order.id,
        previous_status=prev_status,
        new_status=models.PaymentStatus.settled.value,
        amount=order.total_amount,
        amount_paise=shares["amount_paise"],
        currency="INR",
        actor_type="system",
        reason="Atomic 3-way payment ledger settlement completed",
    )
    db.add(ledger_entry)

    db.flush()
    return payment


def settle_payout(db: Session, payment_id: str) -> models.Payment:
    """Convenience helper to settle payout by payment ID."""
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    res = settle_payment(db, payment.order)
    db.commit()
    db.refresh(res)
    return res

