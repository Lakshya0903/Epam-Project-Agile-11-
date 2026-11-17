<<<<<<< HEAD
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
=======
"""
Payments & Gateway Router
Primary Maintainer: Hemant Yadav & Anshika Sharma
Extended for Phase 2:
  - Gateway Checkout Order Initiation
  - Client Signature Verification & Idempotency
  - Webhook Ingestion & Signature Verification
  - Append-Only Audit Ledger Inspection
  - Payout Release Eligibility & Refunds
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.security import get_current_user, require_role
from ..services.payment_engine import (
    initiate_payment,
    verify_payment,
    evaluate_payment_release_eligibility,
    refund_payment,
    get_or_create_payment,
)
from ..services.payment_gateways import get_payment_gateway

router = APIRouter(tags=["payments"])


# ---------- Phase 2: Payment Gateway Integration ----------

@router.post("/payments/orders/{order_id}/initiate", response_model=schemas.PaymentInitiateResponse)
def initiate_order_payment(
    order_id: str,
    payload: Optional[schemas.PaymentInitiateRequest] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Initiate a payment transaction with the selected payment gateway provider."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    provider = payload.provider if payload else None
    idempotency_key = payload.idempotency_key if payload else None
    return initiate_payment(db, order, provider_name=provider, idempotency_key=idempotency_key)


@router.post("/payments/{payment_id}/verify", response_model=schemas.PaymentVerifyResponse)
def verify_payment_endpoint(
    payment_id: str,
    payload: schemas.PaymentVerifyRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Cryptographically verify payment signature returned by gateway upon client checkout."""
    verified_payment = verify_payment(
        db=db,
        payment_id=payment_id,
        gateway_order_id=payload.gateway_order_id,
        gateway_payment_id=payload.gateway_payment_id,
        gateway_signature=payload.gateway_signature,
    )
    return schemas.PaymentVerifyResponse(
        verified=True,
        status=verified_payment.status,
        payment_id=verified_payment.id,
        message="Payment signature verified successfully",
    )


@router.post("/payments/webhooks/{provider}")
async def payment_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None),
):
    """
    Ingest asynchronous webhook callbacks from payment gateway providers
    with cryptographic HMAC signature verification.
    """
    raw_body = await request.body()
    gateway = get_payment_gateway(provider)

    signature = x_razorpay_signature or request.headers.get("X-Signature") or ""
    is_valid = gateway.verify_webhook_signature(raw_body=raw_body, signature_header=signature)

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    return {"status": "ok", "provider": provider, "received": True}


@router.get("/payments/orders/{order_id}", response_model=schemas.PaymentOut)
def get_order_payment(
    order_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Fetch payment and escrow lifecycle status for an order."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return get_or_create_payment(db, order)


@router.get("/payments/{payment_id}", response_model=schemas.PaymentOut)
def get_payment_by_id(
    payment_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Fetch payment by unique ID."""
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.get("/payments/{payment_id}/ledger", response_model=List[schemas.PaymentLedgerEntryOut])
def get_payment_ledger(
    payment_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin, models.UserRole.reviewer)),
):
    """Retrieve immutable append-only ledger entries for a payment record (Admin/Reviewer only)."""
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return (
        db.query(models.PaymentLedgerEntry)
        .filter(models.PaymentLedgerEntry.payment_id == payment_id)
        .order_by(models.PaymentLedgerEntry.created_at.asc())
        .all()
    )


@router.post("/payments/{payment_id}/check-release")
def check_release_eligibility_endpoint(
    payment_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Evaluate whether buyer confirmation window has elapsed and payment is eligible for release."""
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    is_eligible = evaluate_payment_release_eligibility(db, payment)
    return {
        "payment_id": payment.id,
        "is_eligible": is_eligible,
        "current_status": payment.status,
        "is_on_hold": payment.is_on_hold,
        "hold_reason": payment.hold_reason,
        "buyer_confirmation_deadline": payment.buyer_confirmation_deadline,
    }


@router.post("/payments/{payment_id}/refund", response_model=schemas.PaymentOut)
def issue_refund(
    payment_id: str,
    payload: schemas.PaymentRefundRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin, models.UserRole.reviewer)),
):
    """Issue gateway refund for a payment record upon dispute resolution."""
    return refund_payment(db, payment_id, actor=user, amount_inr=payload.amount_inr, reason=payload.reason)


# ---------- Phase 1: Existing Endpoints (Preserved for Backward Compatibility) ----------

@router.get("/orders/{order_id}/payment", response_model=schemas.PaymentOut)
def get_payment_legacy(
    order_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Retrieve settlement payment record for an order (Legacy compatibility path)."""
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
>>>>>>> dab7f05 (feat(payments): implement phase 2 payment gateway)
