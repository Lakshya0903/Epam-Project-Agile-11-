"""
Smart Order Engine
Primary Maintainer: Lakshya Raj Malviya (Backend Lead)

Handles order placement, stock verification, atomic inventory reservation,
demand calculation, and dispatch branching (Bulk vs Individual).
"""

from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..utils.geo import area_key
from .logistics_engine import assign_logistics_for_order
from .batch_engine import try_batch_individual_order


def create_order(db: Session, buyer: models.BuyerProfile, payload: schemas.OrderCreate) -> models.Order:
    """
    Implements: PLACE ORDER -> SAVE ORDER -> SMART ORDER ENGINE
      1. Match farmer/FPO inventory
      2. Check quantity availability
      3. Deduct stock immediately (reserve inventory)
      4. Compute order total
      5. Branch to Bulk direct logistics or Individual smart batching
    """
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item",
        )

    order = models.Order(
        buyer_id=buyer.id,
        order_type=payload.order_type,
        delivery_location=payload.delivery_location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        delivery_slot=payload.delivery_slot,
        status=models.OrderStatus.placed,
    )
    db.add(order)
    db.flush()  # Obtain order.id before creating order items

    total_amount = 0.0
    total_weight = 0.0
    order_items: List[models.OrderItem] = []

    for item in payload.items:
        produce = db.query(models.Produce).filter(models.Produce.id == item.produce_id).first()
        if not produce:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produce item {item.produce_id} not found",
            )
        if produce.status == models.ProduceStatus.sold_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{produce.product_name} is currently sold out",
            )
        if item.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero",
            )
        if produce.quantity_available < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {produce.quantity_available} {produce.unit} of {produce.product_name} available",
            )

        subtotal = round(item.quantity * produce.price_per_unit, 2)
        order_item = models.OrderItem(
            order_id=order.id,
            produce_id=produce.id,
            quantity=item.quantity,
            unit_price=produce.price_per_unit,
            subtotal=subtotal,
        )
        db.add(order_item)
        order_items.append(order_item)

        # Deduct matched inventory immediately (reserve stock)
        produce.quantity_available -= item.quantity
        if produce.quantity_available <= 0:
            produce.quantity_available = 0.0
            produce.status = models.ProduceStatus.sold_out

        total_amount += subtotal
        total_weight += item.quantity

    order.total_amount = round(total_amount, 2)
    order.status = models.OrderStatus.matched
    db.flush()

    # Branch according to order type
    if payload.order_type == models.OrderType.bulk:
        # Direct order processing -> straight to dedicated logistics calculation
        assign_logistics_for_order(db, order, total_weight)
    else:
        # Find nearby individual orders (same area + time slot) for batching
        try_batch_individual_order(db, order, total_weight)

    db.commit()
    db.refresh(order)
    return order
