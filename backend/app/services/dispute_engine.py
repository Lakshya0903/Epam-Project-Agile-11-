"""
Dispute Management Engine
Primary Maintainer: Aparna Jha & Lakshya Raj Malviya
Phase 2: Handles 24-hour post-delivery dispute submission, photo evidence uploads,
private authenticated evidence storage, reviewer workflow, and payment hold integration.
"""

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _ensure_upload_dir():
    """Ensure secure upload storage directory exists."""
    os.makedirs(settings.upload_dir, exist_ok=True)


def submit_dispute(
    db: Session,
    buyer: models.BuyerProfile,
    payload: schemas.DisputeCreate,
) -> models.Dispute:
    """
    Submit a dispute for a delivered order:
      1. Validates order ownership.
      2. Validates order is in DELIVERED state.
      3. Validates submission occurs within 24 hours of delivery.
      4. Prevents duplicate active disputes on the same order.
      5. Places associated payment on hold immediately.
    """
    order = db.query(models.Order).filter(models.Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.buyer_id != buyer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to raise a dispute for this order",
        )

    if order.status not in (models.OrderStatus.delivered, models.OrderStatus.paid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Disputes can only be filed after delivery. Current order status: '{order.status.value}'",
        )

    if not order.delivered_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order delivery timestamp is missing. Cannot verify dispute window.",
        )

    # 24-hour server-side window calculation
    now_utc = datetime.now(timezone.utc)
    del_time = order.delivered_at
    if del_time.tzinfo is None:
        del_time = del_time.replace(tzinfo=timezone.utc)

    max_window = timedelta(hours=settings.dispute_window_hours)
    if (now_utc - del_time) > max_window:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dispute submission window has expired. Disputes must be filed within {settings.dispute_window_hours} hours of delivery.",
        )

    existing = db.query(models.Dispute).filter(models.Dispute.order_id == order.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A dispute (ID: {existing.id}) has already been filed for this order.",
        )

    dispute = models.Dispute(
        order_id=order.id,
        buyer_id=buyer.id,
        reason=payload.reason.value if hasattr(payload.reason, "value") else str(payload.reason),
        description=payload.description.strip(),
        status=models.DisputeStatus.open.value,
    )
    db.add(dispute)
    db.flush()

    # Integrated Payment Protection Hold: Place related payment on hold
    payment = db.query(models.Payment).filter(models.Payment.order_id == order.id).first()
    if payment:
        payment.is_on_hold = True
        payment.hold_reason = f"Dispute #{dispute.id[:8]} filed: {dispute.reason}"
        prev_status = payment.status
        payment.status = models.PaymentStatus.on_hold.value

        ledger_entry = models.PaymentLedgerEntry(
            payment_id=payment.id,
            order_id=order.id,
            previous_status=prev_status,
            new_status=models.PaymentStatus.on_hold.value,
            amount=payment.total_amount,
            amount_paise=payment.amount_paise,
            currency="INR",
            actor_id=buyer.user_id,
            actor_type="buyer",
            reason=f"Payment placed on hold due to dispute submission: {dispute.reason}",
        )
        db.add(ledger_entry)

    db.commit()
    db.refresh(dispute)
    return dispute


def attach_dispute_evidence(
    db: Session,
    dispute_id: str,
    actor: models.User,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
) -> models.DisputeEvidence:
    """
    Validates and securely persists photographic evidence for a dispute:
      1. Verifies dispute exists and actor is authorized.
      2. Validates image extension and MIME type (JPEG, PNG, WebP).
      3. Validates file size against configurable limit (default 5MB).
      4. Generates secure UUID-based filename.
      5. Writes file to private storage outside the public web root.
    """
    dispute = db.query(models.Dispute).filter(models.Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    # Authorization check
    buyer = db.query(models.BuyerProfile).filter(models.BuyerProfile.id == dispute.buyer_id).first()
    if actor.role != models.UserRole.admin and (not buyer or buyer.user_id != actor.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to attach evidence to this dispute")

    # MIME & Extension validation
    clean_mime = mime_type.lower().strip()
    if clean_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{clean_mime}'. Accepted formats: JPEG, PNG, WebP.",
        )

    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Accepted: .jpg, .jpeg, .png, .webp.",
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum permissible size of {settings.max_upload_size_mb} MB",
        )

    _ensure_upload_dir()
    secure_filename = f"{uuid.uuid4()}{ext}"
    storage_path = os.path.join(settings.upload_dir, secure_filename)

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    evidence = models.DisputeEvidence(
        dispute_id=dispute.id,
        file_path=storage_path,
        file_name=os.path.basename(filename),
        mime_type=clean_mime,
        file_size_bytes=len(file_bytes),
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def get_dispute_by_id(db: Session, dispute_id: str, actor: models.User) -> models.Dispute:
    """Retrieve dispute with privacy & access control."""
    dispute = db.query(models.Dispute).filter(models.Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    buyer = db.query(models.BuyerProfile).filter(models.BuyerProfile.id == dispute.buyer_id).first()
    if actor.role not in (models.UserRole.admin, models.UserRole.reviewer):
        if not buyer or buyer.user_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return dispute


def resolve_dispute(
    db: Session,
    dispute_id: str,
    reviewer: models.User,
    payload: schemas.DisputeResolution,
) -> models.Dispute:
    """
    Reviewer/Admin Dispute Resolution Workflow:
      - Validates reviewer permissions (Admin or Reviewer).
      - Records resolution decision & notes.
      - Resolves payment hold accordingly:
          - 'REFUND': Triggers refund flow on payment.
          - 'RELEASE': Releases payment hold, making it eligible for settlement.
          - 'REJECTED': Rejects dispute claim and releases hold.
    """
    if reviewer.role not in (models.UserRole.admin, models.UserRole.reviewer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform administrators or designated reviewers can resolve disputes",
        )

    dispute = db.query(models.Dispute).filter(models.Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    decision = payload.decision.upper().strip()
    if decision not in ("REFUND", "RELEASE", "REJECTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be one of: 'REFUND', 'RELEASE', 'REJECTED'",
        )

    now_utc = datetime.now(timezone.utc)
    dispute.resolution_decision = decision
    dispute.resolution_notes = payload.notes.strip()
    dispute.resolved_by_id = reviewer.id
    dispute.resolved_at = now_utc

    payment = db.query(models.Payment).filter(models.Payment.order_id == dispute.order_id).first()

    if decision == "REFUND":
        dispute.status = models.DisputeStatus.resolved_refund.value
        if payment:
            payment.is_on_hold = False
            prev_status = payment.status
            payment.status = models.PaymentStatus.refunded.value
            payment.refunded_amount_paise = payment.amount_paise

            ledger_entry = models.PaymentLedgerEntry(
                payment_id=payment.id,
                order_id=dispute.order_id,
                previous_status=prev_status,
                new_status=models.PaymentStatus.refunded.value,
                amount=payment.total_amount,
                amount_paise=payment.amount_paise,
                currency="INR",
                actor_id=reviewer.id,
                actor_type="reviewer",
                reason=f"Dispute resolved with full refund: {payload.notes}",
            )
            db.add(ledger_entry)

    elif decision == "RELEASE":
        dispute.status = models.DisputeStatus.resolved_release.value
        if payment:
            payment.is_on_hold = False
            payment.hold_reason = None
            prev_status = payment.status
            payment.status = models.PaymentStatus.eligible_for_release.value

            ledger_entry = models.PaymentLedgerEntry(
                payment_id=payment.id,
                order_id=dispute.order_id,
                previous_status=prev_status,
                new_status=models.PaymentStatus.eligible_for_release.value,
                amount=payment.total_amount,
                amount_paise=payment.amount_paise,
                currency="INR",
                actor_id=reviewer.id,
                actor_type="reviewer",
                reason=f"Dispute resolved in favor of release: {payload.notes}",
            )
            db.add(ledger_entry)

    elif decision == "REJECTED":
        dispute.status = models.DisputeStatus.rejected.value
        if payment:
            payment.is_on_hold = False
            payment.hold_reason = None
            prev_status = payment.status
            payment.status = models.PaymentStatus.eligible_for_release.value

            ledger_entry = models.PaymentLedgerEntry(
                payment_id=payment.id,
                order_id=dispute.order_id,
                previous_status=prev_status,
                new_status=models.PaymentStatus.eligible_for_release.value,
                amount=payment.total_amount,
                amount_paise=payment.amount_paise,
                currency="INR",
                actor_id=reviewer.id,
                actor_type="reviewer",
                reason=f"Dispute rejected by reviewer: {payload.notes}",
            )
            db.add(ledger_entry)

    db.commit()
    db.refresh(dispute)
    return dispute

