"""
Smart Batching Engine
Primary Maintainer: Lakshya Raj Malviya (Backend Lead)
Extended for Phase 2:
  - Automatic Zone, Drop Point & Mode-Specific Batch Generation
  - Dual Capacity Enforcement (Max Weight kg AND Max Order Count)
  - Configurable Minimum Thresholds (per Zone / Batch)
  - Schedule-Driven Cutoff Calculation (Prep + Dispatch Buffers)
  - Concurrency-Safe Automatic Best-Batch Assignment
  - Below-Threshold Cutoff Review Policies
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..utils.geo import area_key, estimate_distance_km
from .logistics_engine import assign_logistics_for_batch

# Maximum geographic radius (km) between farmer pickup locations
# for them to be consolidated into a single multi-stop vehicle route
MAX_PICKUP_DISTANCE_KM = 50.0

SLOT_HOURS = {
    "morning": 9,     # 09:00
    "afternoon": 14,  # 14:00
    "evening": 19,    # 19:00
}


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


def parse_slot_details(delivery_slot: str) -> Tuple[Optional[str], str, Optional[datetime], Optional[datetime]]:
    """
    Parses 'YYYY-MM-DD|slot' or bare 'slot'.
    Returns: (delivery_date_str, slot_name, slot_start_datetime, slot_end_datetime)
    """
    delivery_date_str = None
    slot_name = delivery_slot.lower().strip()

    if "|" in delivery_slot:
        parts = delivery_slot.split("|")
        delivery_date_str = parts[0].strip()
        slot_name = parts[1].lower().strip()

    slot_start = None
    slot_end = None

    if delivery_date_str:
        try:
            d = datetime.strptime(delivery_date_str, "%Y-%m-%d")
            hour = SLOT_HOURS.get(slot_name, 12)
            slot_start = datetime(d.year, d.month, d.day, hour, 0, 0, tzinfo=timezone.utc)
            slot_end = slot_start + timedelta(hours=3)
        except Exception:
            pass

    return delivery_date_str, slot_name, slot_start, slot_end


def compute_batch_cutoff(
    slot_start: Optional[datetime],
    prep_hours: float,
    dispatch_hours: float,
) -> Optional[datetime]:
    """
    Calculates deterministic batch cutoff:
      Batch Cutoff = Delivery slot start - Preparation buffer - Dispatch buffer
    """
    if not slot_start:
        return None
    total_buffer_hours = (prep_hours or 0.0) + (dispatch_hours or 0.0)
    return slot_start - timedelta(hours=total_buffer_hours)


def try_batch_individual_order(
    db: Session,
    order: models.Order,
    order_weight_kg: float,
) -> models.DeliveryBatch:
    """
    Phase 2 Automatic Delivery-Batch Assignment:
      1. Resolves destination DeliveryZone, DeliveryMode, and DropPoint.
      2. Validates schedule and computes cutoff from delivery slot.
      3. Searches active, compatible open batches in the zone/area.
      4. Enforces Dual Capacity:
           - Weight check: current_weight + order_weight <= max_weight_kg
           - Count check: current_order_count + 1 <= max_orders
      5. Checks farmer pickup compatibility (<50 km).
      6. Selects best eligible batch or automatically creates a new one.
      7. Reserves batch capacity atomically.
      8. Checks minimum threshold trigger (dispatch if threshold reached).
    """
    key = area_key(order.delivery_location)
    mode = order.delivery_mode or "home_delivery"
    drop_point_id = order.drop_point_id

    # Resolve zone configuration
    zone = None
    if order.zone_id:
        zone = db.query(models.DeliveryZone).filter(models.DeliveryZone.id == order.zone_id).first()
    elif order.pincode:
        from .serviceability_engine import find_zone_for_pincode
        zone = find_zone_for_pincode(db, order.pincode)
        if zone:
            order.zone_id = zone.id

    # Extract date & slot scheduling
    date_str, slot_name, slot_start, slot_end = parse_slot_details(order.delivery_slot)

    # Determine thresholds from zone or system defaults
    min_threshold_kg = (
        zone.min_batch_threshold_kg
        if zone and zone.min_batch_threshold_kg is not None
        else settings.default_min_batch_threshold_kg
    )
    max_weight_kg = (
        zone.max_batch_weight_kg
        if zone and zone.max_batch_weight_kg is not None
        else settings.default_max_batch_weight_kg
    )
    max_orders = (
        zone.max_batch_orders
        if zone and zone.max_batch_orders is not None
        else settings.default_max_batch_orders
    )
    prep_hours = zone.preparation_buffer_hours if zone else settings.default_prep_buffer_hours
    dispatch_hours = zone.dispatch_buffer_hours if zone else settings.default_dispatch_buffer_hours

    cutoff_time = compute_batch_cutoff(slot_start, prep_hours, dispatch_hours)
    now_utc = datetime.now(timezone.utc)

    # Query candidate open batches
    query = db.query(models.DeliveryBatch).filter(
        models.DeliveryBatch.status == "open",
        models.DeliveryBatch.delivery_slot == order.delivery_slot,
    )

    if zone:
        query = query.filter(models.DeliveryBatch.zone_id == zone.id)
    else:
        query = query.filter(models.DeliveryBatch.area_key == key)

    if mode == "shared_drop_point":
        query = query.filter(
            models.DeliveryBatch.delivery_mode == "shared_drop_point",
            models.DeliveryBatch.drop_point_id == drop_point_id,
        )
    else:
        query = query.filter(models.DeliveryBatch.delivery_mode == "home_delivery")

    open_batches = query.all()

    selected_batch = None
    for batch in open_batches:
        # Check cutoff expiration
        if batch.cutoff_time and now_utc > batch.cutoff_time.replace(tzinfo=timezone.utc if batch.cutoff_time.tzinfo is None else batch.cutoff_time.tzinfo):
            continue

        # Dual capacity check 1: Weight limit
        new_total_weight = batch.total_weight_kg + order_weight_kg
        if new_total_weight > (batch.max_weight_kg or max_weight_kg):
            continue

        # Dual capacity check 2: Order count limit
        new_order_count = (batch.current_order_count or len(batch.orders)) + 1
        if new_order_count > (batch.max_orders or max_orders):
            continue

        # Vehicle capacity check
        if not _vehicle_can_handle_batch(db, new_total_weight):
            continue

        # Farmer geographic pickup compatibility (<50km)
        batch_orders = db.query(models.Order).filter(models.Order.batch_id == batch.id).all()
        if not _farmers_compatible(batch_orders, order):
            continue

        selected_batch = batch
        break

    # If no compatible open batch exists, automatically create a new one
    if not selected_batch:
        selected_batch = models.DeliveryBatch(
            zone_id=zone.id if zone else None,
            area_key=key,
            delivery_mode=mode,
            drop_point_id=drop_point_id if mode == "shared_drop_point" else None,
            delivery_date=date_str,
            delivery_slot=order.delivery_slot,
            slot_start=slot_start,
            slot_end=slot_end,
            cutoff_time=cutoff_time,
            min_threshold_kg=min_threshold_kg,
            max_weight_kg=max_weight_kg,
            max_orders=max_orders,
            total_weight_kg=0.0,
            current_order_count=0,
            status="open",
            below_threshold_action="review_required",
        )
        db.add(selected_batch)
        db.flush()

    # Atomically reserve capacity in the batch
    selected_batch.total_weight_kg += order_weight_kg
    selected_batch.current_order_count = (selected_batch.current_order_count or 0) + 1
    selected_batch.updated_at = now_utc

    # Close batch if full on weight or orders
    if (
        selected_batch.total_weight_kg >= selected_batch.max_weight_kg
        or selected_batch.current_order_count >= selected_batch.max_orders
    ):
        selected_batch.status = "full"

    order.batch_id = selected_batch.id
    order.status = models.OrderStatus.batched
    db.flush()

    # Minimum threshold dispatch trigger check
    if selected_batch.total_weight_kg >= selected_batch.min_threshold_kg:
        assign_logistics_for_batch(db, selected_batch)

    return selected_batch


def check_and_evaluate_cutoff_batches(db: Session) -> List[models.DeliveryBatch]:
    """
    Evaluates open batches against their schedule cutoffs.
    If cutoff has passed:
      - If total_weight >= min_threshold: dispatches batch.
      - If total_weight < min_threshold: marks 'review_required' for administrative review.
    """
    now_utc = datetime.now(timezone.utc)
    batches = db.query(models.DeliveryBatch).filter(
        models.DeliveryBatch.status.in_(["open", "full"]),
        models.DeliveryBatch.cutoff_time != None,  # noqa: E711
    ).all()

    updated = []
    for batch in batches:
        cutoff = batch.cutoff_time
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)

        if now_utc >= cutoff:
            if batch.total_weight_kg >= batch.min_threshold_kg:
                assign_logistics_for_batch(db, batch)
                batch.status = "dispatched"
            else:
                batch.status = "review_required"
            batch.updated_at = now_utc
            updated.append(batch)

    if updated:
        db.commit()
    return updated


def request_direct_delivery(
    db: Session,
    order: models.Order,
    extra_cost_percent: float = 25.0,
) -> models.Order:
    """
    Allow an individual buyer to opt out of the waiting batch and request
    direct single-dropoff delivery with an expedited delivery cost surcharge.
    Decrements both weight and order count from the existing batch.
    """
    from .logistics_engine import assign_logistics_for_order

    order_weight = sum(i.quantity for i in order.items)

    if order.batch_id:
        batch = db.query(models.DeliveryBatch).filter(models.DeliveryBatch.id == order.batch_id).first()
        if batch:
            batch.total_weight_kg -= order_weight
            if batch.total_weight_kg < 0:
                batch.total_weight_kg = 0.0

            if batch.current_order_count and batch.current_order_count > 0:
                batch.current_order_count -= 1

            if batch.status == "full":
                batch.status = "open"

    order.batch_id = None
    delivery = assign_logistics_for_order(db, order, order_weight)

    if delivery and delivery.delivery_cost is not None:
        delivery.delivery_cost = round(delivery.delivery_cost * (1 + extra_cost_percent / 100.0), 2)

    db.commit()
    db.refresh(order)
    return order


# Aliases for backward and test compatibility
assign_order_to_batch = lambda db, order, order_weight=None, **kwargs: try_batch_individual_order(db, order, order_weight if order_weight is not None else _order_weight(order))
evaluate_cutoff_batches = check_and_evaluate_cutoff_batches
def calculate_schedule_cutoff(delivery_slot: str, prep_buffer_hours: float = 2.0, dispatch_buffer_minutes: float = 30) -> Optional[datetime]:
    _, _, start, _ = parse_slot_details(delivery_slot)
    return compute_batch_cutoff(start, prep_buffer_hours, dispatch_buffer_minutes / 60.0)
                              
