"""
Produce Catalog Business Logic & Service Engine
Primary Maintainer: Yash Goyal (Backend Developer)

Encapsulates produce validation, catalog search, farmer listing queries,
and inventory status management.
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas


def create_produce(
    db: Session,
    farmer: models.FarmerProfile,
    payload: schemas.ProduceCreate,
) -> models.Produce:
    """Validate produce creation payload and persist new harvest listing."""
    if payload.price_per_unit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price per unit must be greater than zero",
        )
    if payload.quantity_available <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity available must be greater than zero",
        )

    produce = models.Produce(
        farmer_id=farmer.id,
        product_name=payload.product_name.strip(),
        quantity_available=payload.quantity_available,
        unit=payload.unit or "kg",
        quality_grade=payload.quality_grade or "A",
        price_per_unit=payload.price_per_unit,
        available_date=payload.available_date or datetime.now(timezone.utc),
        pickup_location=payload.pickup_location.strip(),
        latitude=payload.latitude if payload.latitude is not None else farmer.latitude,
        longitude=payload.longitude if payload.longitude is not None else farmer.longitude,
        status=models.ProduceStatus.available,
    )
    db.add(produce)
    db.commit()
    db.refresh(produce)
    return produce


def search_marketplace(
    db: Session,
    product_name: Optional[str] = None,
) -> List[models.Produce]:
    """Retrieve all available produce matching optional name query."""
    query = db.query(models.Produce).filter(models.Produce.status == models.ProduceStatus.available)
    if product_name:
        query = query.filter(models.Produce.product_name.ilike(f"%{product_name.strip()}%"))
    return query.order_by(models.Produce.created_at.desc()).all()


def list_farmer_produce(
    db: Session,
    farmer_id: str,
) -> List[models.Produce]:
    """List all produce items listed by a specific farmer."""
    return (
        db.query(models.Produce)
        .filter(models.Produce.farmer_id == farmer_id)
        .order_by(models.Produce.created_at.desc())
        .all()
    )


def get_produce_by_id(
    db: Session,
    produce_id: str,
) -> models.Produce:
    """Retrieve produce item by ID; raise HTTP 404 if not found."""
    produce = db.query(models.Produce).filter(models.Produce.id == produce_id).first()
    if not produce:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produce item not found",
        )
    return produce
