"""
Logistics Engine: Fleet Selection & Multi-Stop Route Optimization
Primary Maintainer: Hemant Yadav (Backend Developer 3)
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from .. import models
from ..utils.geo import estimate_distance_km
from ..utils.otp import generate_otp

COLD_CHAIN_KEYWORDS = {
    "milk",
    "paneer",
    "curd",
    "yogurt",
    "meat",
    "fish",
    "chicken",
    "egg",
    "cream",
}


def _requires_cold_chain(order: models.Order) -> bool:
    """Determine whether any items in the order necessitate temperature-controlled transport."""
    for item in order.items:
        name = (item.produce.product_name or "").lower()
        if any(kw in name for kw in COLD_CHAIN_KEYWORDS):
            return True
    return False


def _find_best_partner(
    db: Session,
    weight_kg: float,
    distance_km: float,
    need_cold_chain: bool,
) -> Optional[models.LogisticsPartner]:
    """Identify the most cost-effective and highly-rated available vehicle partner."""
    query = db.query(models.LogisticsPartner).filter(
        models.LogisticsPartner.is_available == True,  # noqa: E712
        models.LogisticsPartner.capacity_kg >= weight_kg,
    )

    if need_cold_chain:
        query = query.filter(models.LogisticsPartner.supports_cold_chain == True)  # noqa: E712

    candidates = query.all()

    # Fallback to available fleet if exact match is empty
    if not candidates:
        candidates = (
            db.query(models.LogisticsPartner)
            .filter(models.LogisticsPartner.is_available == True)  # noqa: E712
            .all()
        )

    if not candidates:
        return None

    def total_cost(partner: models.LogisticsPartner) -> float:
        return partner.base_cost + partner.cost_per_km * distance_km

    # Sort by lowest freight cost, breaking ties with partner rating
    candidates.sort(key=lambda p: (total_cost(p), -p.rating))
    return candidates[0]


def _order_weight(order: models.Order) -> float:
    return sum(item.quantity for item in order.items)


def _order_pickup_points(order: models.Order) -> List[Tuple[str, Optional[float], Optional[float]]]:
    """Extract unique farmer pickup points associated with items in an order."""
    points = []
    seen = set()

    for item in order.items:
        produce = item.produce
        if not produce or not produce.farmer:
            continue
        farmer = produce.farmer
        key = (farmer.id, farmer.pickup_location)
        if key in seen:
            continue
        seen.add(key)
        points.append((farmer.pickup_location, farmer.latitude, farmer.longitude))

    return points


def _distance_between_points(
    point_a: Tuple[str, Optional[float], Optional[float]],
    point_b: Tuple[str, Optional[float], Optional[float]],
) -> float:
    return estimate_distance_km(
        point_a[1], point_a[2],
        point_b[1], point_b[2],
        point_a[0], point_b[0],
    )


def _optimize_batch_route(orders: List[models.Order]) -> Tuple[List[str], float]:
    """
    NEAREST-NEIGHBOUR MULTI-STOP ROUTE HEURISTIC:
      1. Collect and visit unique farmer pickup points first.
      2. Sequence buyer dropoff points nearest to the final pickup point.
      3. Return consolidated route label and total distance (km).
    """
    pickup_points = []
    seen_pickups = set()

    for order in orders:
        for point in _order_pickup_points(order):
            key = (point[0], point[1], point[2])
            if key not in seen_pickups:
                seen_pickups.add(key)
                pickup_points.append(point)

    if not pickup_points:
        pickup_points = [("Depot", None, None)]

    delivery_points = [
        (order.delivery_location, order.latitude, order.longitude, order.id)
        for order in orders
    ]

    route_labels = []
    total_distance = 0.0

    # Phase 1: Optimize farmer pickups
    current_pickup = pickup_points[0]
    route_labels.append(current_pickup[0])
    remaining_pickups = pickup_points[1:]

    while remaining_pickups:
        nearest = min(remaining_pickups, key=lambda p: _distance_between_points(current_pickup, p))
        total_distance += _distance_between_points(current_pickup, nearest)
        current_pickup = nearest
        route_labels.append(nearest[0])
        remaining_pickups.remove(nearest)

    # Phase 2: Sequence buyer delivery dropoffs
    current_location = current_pickup
    remaining_deliveries = delivery_points.copy()

    while remaining_deliveries:
        nearest_delivery = min(
            remaining_deliveries,
            key=lambda d: estimate_distance_km(
                current_location[1], current_location[2],
                d[1], d[2],
                current_location[0], d[0],
            ),
        )
        total_distance += estimate_distance_km(
            current_location[1], current_location[2],
            nearest_delivery[1], nearest_delivery[2],
            current_location[0], nearest_delivery[0],
        )
        route_labels.append(nearest_delivery[0])
        current_location = (nearest_delivery[0], nearest_delivery[1], nearest_delivery[2])
        remaining_deliveries.remove(nearest_delivery)

    return route_labels, round(total_distance, 2)


def assign_logistics_for_order(
    db: Session,
    order: models.Order,
    weight_kg: float,
) -> Optional[models.Delivery]:
    """DIRECT DELIVERY: Assigned directly for bulk orders or direct-delivery overrides."""
    anchor_produce = order.items[0].produce if order.items else None
    farmer = anchor_produce.farmer if anchor_produce else None

    distance = estimate_distance_km(
        farmer.latitude if farmer else None,
        farmer.longitude if farmer else None,
        order.latitude,
        order.longitude,
        farmer.pickup_location if farmer else "Depot",
        order.delivery_location,
    )

    need_cold_chain = _requires_cold_chain(order)
    partner = _find_best_partner(db, weight_kg, distance, need_cold_chain)

    existing = db.query(models.Delivery).filter(models.Delivery.order_id == order.id).first()
    if existing:
        db.delete(existing)
        db.flush()

    delivery_cost = None
    partner_id = None
    if partner:
        delivery_cost = round(partner.base_cost + partner.cost_per_km * distance, 2)
        partner_id = partner.id

    pickup_label = farmer.pickup_location if farmer else "Depot"
    delivery = models.Delivery(
        order_id=order.id,
        logistics_partner_id=partner_id,
        delivery_mode=order.delivery_mode or "home_delivery",
        drop_point_id=order.drop_point_id,
        distance_km=distance,
        delivery_cost=delivery_cost,
        otp=generate_otp(),
        status=(models.DeliveryStatus.assigned if partner else models.DeliveryStatus.pending),
        route_sequence=f"{pickup_label} -> {order.delivery_location}",
    )
    db.add(delivery)
    order.status = models.OrderStatus.out_for_delivery if partner else models.OrderStatus.matched
    db.flush()
    return delivery


def assign_logistics_for_batch(
    db: Session,
    batch: models.DeliveryBatch,
) -> None:
    """BATCH DELIVERY: Assigns single consolidated vehicle route and splits freight by weight."""
    orders: List[models.Order] = db.query(models.Order).filter(models.Order.batch_id == batch.id).all()
    if not orders:
        return

    route_labels, total_distance = _optimize_batch_route(orders)
    need_cold_chain = any(_requires_cold_chain(order) for order in orders)

    partner = _find_best_partner(db, batch.total_weight_kg, total_distance, need_cold_chain)
    if not partner:
        return

    batch.logistics_partner_id = partner.id
    batch.status = "dispatched"

    total_cost = round(partner.base_cost + partner.cost_per_km * total_distance, 2)
    total_weight = sum(_order_weight(order) for order in orders) or 1.0
    route_sequence = " -> ".join(route_labels)

    for order in orders:
        order_weight = _order_weight(order)
        share_cost = round(total_cost * (order_weight / total_weight), 2)

        existing = db.query(models.Delivery).filter(models.Delivery.order_id == order.id).first()
        if existing:
            db.delete(existing)
            db.flush()

        delivery = models.Delivery(
            order_id=order.id,
            logistics_partner_id=partner.id,
            delivery_mode=batch.delivery_mode or order.delivery_mode or "home_delivery",
            drop_point_id=batch.drop_point_id or order.drop_point_id,
            distance_km=round(total_distance * (order_weight / total_weight), 2),
            delivery_cost=share_cost,
            otp=generate_otp(),
            status=models.DeliveryStatus.assigned,
            route_sequence=route_sequence,
        )
        db.add(delivery)
        order.status = models.OrderStatus.out_for_delivery

    db.flush()
