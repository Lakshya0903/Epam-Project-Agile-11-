"""
Disputes & Evidence Management Router
Primary Maintainer: Aparna Jha & Lakshya Raj Malviya
Phase 2: Complete Dispute lifecycle with private evidence storage and reviewer resolution.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.security import get_current_user, require_role
from ..services.dispute_engine import (
    submit_dispute,
    attach_dispute_evidence,
    get_dispute_by_id,
    resolve_dispute,
)

router = APIRouter(prefix="/disputes", tags=["disputes"])


def _buyer_profile(db: Session, user: models.User) -> models.BuyerProfile:
    profile = db.query(models.BuyerProfile).filter(models.BuyerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Buyer profile not found")
    return profile


@router.post("", response_model=schemas.DisputeOut, status_code=status.HTTP_201_CREATED)
def file_dispute(
    payload: schemas.DisputeCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.buyer, models.UserRole.admin)),
):
    """File a formal dispute within 24 hours of delivery confirmation."""
    buyer = _buyer_profile(db, user) if user.role == models.UserRole.buyer else None
    if not buyer and user.role == models.UserRole.admin:
        order = db.query(models.Order).filter(models.Order.id == payload.order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        buyer = order.buyer

    return submit_dispute(db, buyer, payload)


@router.post("/{dispute_id}/evidence", response_model=schemas.DisputeEvidenceOut, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    dispute_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Upload validated photographic evidence for an active dispute."""
    content = await file.read()
    return attach_dispute_evidence(
        db=db,
        dispute_id=dispute_id,
        actor=user,
        file_bytes=content,
        filename=file.filename or "evidence.jpg",
        mime_type=file.content_type or "image/jpeg",
    )


@router.get("", response_model=List[schemas.DisputeOut])
def list_disputes(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """List disputes with role-based filtering (Admins & Reviewers see all; Buyers see own)."""
    query = db.query(models.Dispute)
    if user.role == models.UserRole.buyer:
        buyer = _buyer_profile(db, user)
        query = query.filter(models.Dispute.buyer_id == buyer.id)
    elif user.role not in (models.UserRole.admin, models.UserRole.reviewer):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if status_filter:
        query = query.filter(models.Dispute.status == status_filter.upper())

    return query.order_by(models.Dispute.created_at.desc()).all()


@router.get("/mine", response_model=List[schemas.DisputeOut])
def my_disputes(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.buyer)),
):
    """Fetch all disputes submitted by the authenticated buyer."""
    buyer = _buyer_profile(db, user)
    return (
        db.query(models.Dispute)
        .filter(models.Dispute.buyer_id == buyer.id)
        .order_by(models.Dispute.created_at.desc())
        .all()
    )


@router.get("/{dispute_id}", response_model=schemas.DisputeOut)
def get_dispute(
    dispute_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Fetch single dispute detail with evidence attachments."""
    return get_dispute_by_id(db, dispute_id, user)


@router.get("/{dispute_id}/evidence/{evidence_id}")
def download_evidence(
    dispute_id: str,
    evidence_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Private, authenticated retrieval of dispute evidence photo."""
    dispute = get_dispute_by_id(db, dispute_id, user)
    evidence = (
        db.query(models.DisputeEvidence)
        .filter(models.DisputeEvidence.id == evidence_id, models.DisputeEvidence.dispute_id == dispute.id)
        .first()
    )
    if not evidence or not os.path.exists(evidence.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found")

    return FileResponse(evidence.file_path, media_type=evidence.mime_type, filename=evidence.file_name)


@router.post("/{dispute_id}/assign", response_model=schemas.DisputeOut)
def assign_reviewer(
    dispute_id: str,
    reviewer_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin)),
):
    """Assign designated reviewer to an active dispute."""
    dispute = db.query(models.Dispute).filter(models.Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    reviewer = db.query(models.User).filter(models.User.id == reviewer_id).first()
    if not reviewer or reviewer.role not in (models.UserRole.reviewer, models.UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user must possess the 'reviewer' or 'admin' role",
        )

    dispute.assigned_reviewer_id = reviewer.id
    dispute.status = models.DisputeStatus.under_review.value
    db.commit()
    db.refresh(dispute)
    return dispute


@router.post("/{dispute_id}/resolve", response_model=schemas.DisputeOut)
def resolve_dispute_endpoint(
    dispute_id: str,
    payload: schemas.DisputeResolution,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.admin, models.UserRole.reviewer)),
):
    """Resolve dispute (REFUND, RELEASE, or REJECTED) and update financial hold."""
    return resolve_dispute(db, dispute_id, user, payload)

