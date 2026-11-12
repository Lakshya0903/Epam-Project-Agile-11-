"""
Produce Endpoints Router
Primary Maintainer: Yash Goyal (Backend Developer)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.security import get_current_user, require_role
from ..services.produce_engine import (
    create_produce,
    search_marketplace,
    list_farmer_produce,
    get_produce_by_id,
)

router = APIRouter(prefix="/produce", tags=["produce"])


def _farmer_profile(db: Session, user: models.User) -> models.FarmerProfile:
    """Helper to verify and retrieve the FarmerProfile for current user."""
    profile = db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Farmer profile not found for this account",
        )
    return profile


@router.post("", response_model=schemas.ProduceOut, status_code=status.HTTP_201_CREATED)
def add_produce(
    payload: schemas.ProduceCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.farmer)),
):
    """ADD PRODUCE DETAILS -> LIST ON PLATFORM (Farmer only)."""
    farmer = _farmer_profile(db, user)
    return create_produce(db, farmer, payload)


@router.get("", response_model=List[schemas.ProduceOut])
def browse_marketplace(
    product_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """BUYER MARKETPLACE: Browse available produce with optional search."""
    return search_marketplace(db, product_name)


@router.get("/mine", response_model=List[schemas.ProduceOut])
def my_produce(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(models.UserRole.farmer)),
):
    """Fetch all produce items listed by the currently authenticated farmer."""
    farmer = _farmer_profile(db, user)
    return list_farmer_produce(db, farmer.id)


@router.get("/{produce_id}", response_model=schemas.ProduceOut)
def get_produce(produce_id: str, db: Session = Depends(get_db)):
    """Fetch a single produce item by its unique ID."""
    return get_produce_by_id(db, produce_id)
