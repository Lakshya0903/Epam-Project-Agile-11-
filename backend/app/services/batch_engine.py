"""
Smart Batching Engine
Primary Maintainer: Lakshya Raj Malviya (Backend Lead)

Groups individual orders by geographic area key and delivery slot,
enforces minimum batch weight thresholds (25 kg), verifies farmer pickup
compatibility, and manages direct delivery overrides.
"""

from typing import List
from sqlalchemy.orm import Session

from .. import models
from ..utils.geo import area_key, estimate_distance_km
from .logistics_engine import assign_logistics_for_batch

# Minimum combined weight required to trigger vehicle dispatch
MIN_BATCH_WEIGHT_KG = 25.0

# Maximum geographic radius (km) between farmer pickup locations
# for them to be consolidated into a single multi-stop vehicle route
MAX_PICKUP_DISTANCE_KM = 50.0


def _order_weight(order: models.Order) -> float:
    """Return total weight of items in an order."""
    return sum(item.quantity for item in order.items)


def _order_farmers(order: models.Order) -> List[models.FarmerProfile]:
    """Return the unique farmer profiles supplying produce for an order."""
    farmers = []
    for item in order.items:
        if item.produce and item.produce.farmer:
            farmer = item.produce.farmer
            if farmer.id not in [f.id for f in farmers]:
                farmers.append(farmer)
    return farmers


def _farmers_compatible(batch_orders: List[models.Order], new_order: models.Order) -> bool:
    """
    Check whether farmer pickup locations are close enough (<50km)
    to be collected on a single consolidated logistics route.
    """
    existing_farmers = []
    for order in batch_orders:
        for farmer in _order_farmers(order):
            if farmer.id not in [f.id for f in existing_farmers]:
                existing_farmers.append(farmer)

    new_farmers = _order_farmers(new_order)
    all_farmers = existing_farmers + [f for f in new_farmers if f.id not in [x.id for x in existing_farmers]]

    for i in range(len(all_farmers)):
        for j in range(i + 1, len(all_farmers)):
            f1 = all_farmers[i]
            f2 = all_farmers[j]
            distance = estimate_distance_km(
                f1.latitude,
                f1.longitude,
                f2.latitude,
                f2.longitude,
                f1.pickup_location,
                f2.pickup_location,
            )
            if distance > MAX_PICKUP_DISTANCE_KM:
                return False

    return True


def _vehicle_can_handle_batch(db: Session, total_weight_kg: float) -> bool:
    """Verify that at least one available fleet vehicle has sufficient capacity."""
    partner = (
        db.query(models.LogisticsPartner)
        .filter(
            models.LogisticsPartner.is_available == True,  # noqa: E712
            models.LogisticsPartner.capacity_kg >= total_weight_kg,
        )
        .first()
    )
    return partner is not None


def try_batch_individual_order(
    db: Session,
    order: models.Order,
    order_weight_kg: float,
) -> models.DeliveryBatch:
    """
    Evaluate and assign an individual order to a matching open delivery batch:
      1. Destination area key match (locality)
      2. Delivery time slot match
      3. Farmer pickup compatibility (<50km)
      4. Fleet vehicle capacity sufficiency
      5. Minimum 25 kg dispatch trigger
    """
    key = area_key(order.delivery_location)

    open_batches = (
        db.query(models.DeliveryBatch)
        .filter(
            models.DeliveryBatch.area_key == key,
            models.DeliveryBatch.delivery_slot == order.delivery_slot,
            models.DeliveryBatch.status == "open",
        )
        .all()
    )

    selected_batch = None
    for batch in open_batches:
        batch_orders = db.query(models.Order).filter(models.Order.batch_id == batch.id).all()
        new_total_weight = batch.total_weight_kg + order_weight_kg

        if not _vehicle_can_handle_batch(db, new_total_weight):
            continue
        if not _farmers_compatible(batch_orders, order):
            continue

        selected_batch = batch
        break

    # If no compatible open batch exists, create a new one
    if not selected_batch:
        selected_batch = models.DeliveryBatch(
            area_key=key,
            delivery_slot=order.delivery_slot,
            status="open",
            total_weight_kg=0.0,
        )
        db.add(selected_batch)
        db.flush()

    # Assign order to the batch
    selected_batch.total_weight_kg += order_weight_kg
    order.batch_id = selected_batch.id
    order.status = models.OrderStatus.batched
    db.flush()

    # Dispatch trigger check
    if selected_batch.total_weight_kg >= MIN_BATCH_WEIGHT_KG:
        assign_logistics_for_batch(db, selected_batch)

    return selected_batch


def request_direct_delivery(
    db: Session,
    order: models.Order,
    extra_cost_percent: float = 25.0,
) -> models.Order:
    """
    Allow an individual buyer to opt out of the waiting batch and request
    direct single-dropoff delivery with an expedited delivery cost surcharge.
    """
    from .logistics_engine import assign_logistics_for_order

    if order.batch_id:
        batch = db.query(models.DeliveryBatch).filter(models.DeliveryBatch.id == order.batch_id).first()
        if batch:
            batch.total_weight_kg -= sum(i.quantity for i in order.items)
            if batch.total_weight_kg < 0:
                batch.total_weight_kg = 0.0

    order.batch_id = None

    order_weight = sum(i.quantity for i in order.items)
    delivery = assign_logistics_for_order(db, order, order_weight)

    if delivery and delivery.delivery_cost is not None:
        delivery.delivery_cost = round(delivery.delivery_cost * (1 + extra_cost_percent / 100.0), 2)

    db.commit()
    db.refresh(order)
    return order
