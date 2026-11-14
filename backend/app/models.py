"""
SQLAlchemy Database ORM Models
Primary Maintainer: Swyam Shukla (Database Lead)
Extended for Phase 2: Nationwide Delivery Zones, Shared Drop Points,
5-State Order Lifecycle, Disputes, and Payment Ledger.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey,
    Enum as SAEnum, Text
)
from sqlalchemy.orm import relationship

from .database import Base


def gen_uuid():
    return str(uuid.uuid4())


# ---------- Enumerations ----------

class UserRole(str, enum.Enum):
    farmer = "farmer"
    buyer = "buyer"
    logistics = "logistics"
    admin = "admin"
    reviewer = "reviewer"


class BuyerType(str, enum.Enum):
    individual = "individual"
    bulk = "bulk"


class ProduceStatus(str, enum.Enum):
    available = "available"
    reserved = "reserved"
    sold_out = "sold_out"


class OrderType(str, enum.Enum):
    individual = "individual"
    bulk = "bulk"


class DeliveryMode(str, enum.Enum):
    home_delivery = "home_delivery"
    shared_drop_point = "shared_drop_point"


class OrderStatus(str, enum.Enum):
    # Phase 2 Canonical 5-State Lifecycle (supports both lowercase & uppercase)
    placed = "placed"
    confirmed = "confirmed"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"

    # Phase 1 Compatibility States
    matched = "matched"
    batched = "batched"
    out_for_delivery = "out_for_delivery"
    paid = "paid"
    cancelled = "cancelled"


class VehicleType(str, enum.Enum):
    truck = "truck"
    mini_truck = "mini_truck"
    van = "van"
    bike = "bike"


class DeliveryStatus(str, enum.Enum):
    pending = "pending"
    assigned = "assigned"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"


class DisputeStatus(str, enum.Enum):
    open = "OPEN"
    under_review = "UNDER_REVIEW"
    resolved_refund = "RESOLVED_REFUND"
    resolved_release = "RESOLVED_RELEASE"
    rejected = "REJECTED"
    cancelled = "CANCELLED"


class DisputeReason(str, enum.Enum):
    quality_issue = "QUALITY_ISSUE"
    damaged_produce = "DAMAGED_PRODUCE"
    missing_items = "MISSING_ITEMS"
    wrong_items = "WRONG_ITEMS"
    late_delivery = "LATE_DELIVERY"
    other = "OTHER"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    payment_initiated = "payment_initiated"
    paid = "paid"
    awaiting_buyer_confirmation = "awaiting_buyer_confirmation"
    eligible_for_release = "eligible_for_release"
    on_hold = "on_hold"
    disputed = "disputed"
    refund_pending = "refund_pending"
    refunded = "refunded"
    settlement_pending = "settlement_pending"
    settled = "settled"
    failed = "failed"
    cancelled = "cancelled"


# ---------- Core Entities ----------

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False)
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False)


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    farm_or_fpo_name = Column(String, nullable=False)
    pickup_location = Column(String, nullable=False)
    address_line = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    user = relationship("User", back_populates="farmer_profile")
    produce_items = relationship("Produce", back_populates="farmer")


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    buyer_type = Column(SAEnum(BuyerType), nullable=False)
    business_name = Column(String, nullable=True)
    default_location = Column(String, nullable=True)
    address_line = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    user = relationship("User", back_populates="buyer_profile")


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False, unique=True)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    city = Column(String, nullable=True)
    serviceable_pincodes = Column(Text, nullable=False)  # JSON or comma-separated list of 6-digit PIN codes
    is_active = Column(Boolean, default=True)
    min_batch_threshold_kg = Column(Float, default=25.0)
    max_batch_weight_kg = Column(Float, default=1000.0)
    max_batch_orders = Column(Integer, default=50)
    preparation_buffer_hours = Column(Float, default=4.0)
    dispatch_buffer_hours = Column(Float, default=2.0)
    allows_home_delivery = Column(Boolean, default=True)
    allows_drop_point = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    drop_points = relationship("SharedDropPoint", back_populates="zone", cascade="all, delete-orphan")
    batches = relationship("DeliveryBatch", back_populates="zone")


class SharedDropPoint(Base):
    __tablename__ = "shared_drop_points"

    id = Column(String, primary_key=True, default=gen_uuid)
    zone_id = Column(String, ForeignKey("delivery_zones.id"), nullable=False)
    name = Column(String, nullable=False)
    address_line = Column(String, nullable=False)
    locality = Column(String, nullable=True)
    city = Column(String, nullable=False)
    district = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    operating_hours = Column(String, default="08:00 - 20:00")
    contact_phone = Column(String, nullable=True)
    capacity_orders = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    zone = relationship("DeliveryZone", back_populates="drop_points")
    batches = relationship("DeliveryBatch", back_populates="drop_point")
    orders = relationship("Order", back_populates="drop_point")


class Produce(Base):
    __tablename__ = "produce"

    id = Column(String, primary_key=True, default=gen_uuid)
    farmer_id = Column(String, ForeignKey("farmer_profiles.id"), nullable=False)
    product_name = Column(String, nullable=False)
    quantity_available = Column(Float, nullable=False)
    unit = Column(String, default="kg")
    quality_grade = Column(String, default="A")
    price_per_unit = Column(Float, nullable=False)
    available_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    pickup_location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(SAEnum(ProduceStatus), default=ProduceStatus.available)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    farmer = relationship("FarmerProfile", back_populates="produce_items")
    order_items = relationship("OrderItem", back_populates="produce")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=gen_uuid)
    buyer_id = Column(String, ForeignKey("buyer_profiles.id"), nullable=False)
    order_type = Column(SAEnum(OrderType), nullable=False)
    delivery_mode = Column(String, default="home_delivery")  # home_delivery | shared_drop_point
    delivery_location = Column(String, nullable=False)
    address_line = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    delivery_slot = Column(String, nullable=False)  # Format: "YYYY-MM-DD|slot"
    status = Column(SAEnum(OrderStatus), default=OrderStatus.placed)
    total_amount = Column(Float, default=0.0)
    batch_id = Column(String, ForeignKey("delivery_batches.id"), nullable=True)
    zone_id = Column(String, ForeignKey("delivery_zones.id"), nullable=True)
    drop_point_id = Column(String, ForeignKey("shared_drop_points.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    processing_at = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    buyer = relationship("BuyerProfile")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    batch = relationship("DeliveryBatch", back_populates="orders")
    zone = relationship("DeliveryZone")
    drop_point = relationship("SharedDropPoint", back_populates="orders")
    delivery = relationship("Delivery", back_populates="order", uselist=False)
    payment = relationship("Payment", back_populates="order", uselist=False)
    dispute = relationship("Dispute", back_populates="order", uselist=False)
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    produce_id = Column(String, ForeignKey("produce.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    produce = relationship("Produce", back_populates="order_items")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    actor_id = Column(String, nullable=True)
    actor_role = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    order = relationship("Order", back_populates="status_history")


class DeliveryBatch(Base):
    __tablename__ = "delivery_batches"

    id = Column(String, primary_key=True, default=gen_uuid)
    zone_id = Column(String, ForeignKey("delivery_zones.id"), nullable=True)
    area_key = Column(String, nullable=False)       # Coarse locality or zone identifier
    delivery_mode = Column(String, default="home_delivery")  # home_delivery | shared_drop_point
    drop_point_id = Column(String, ForeignKey("shared_drop_points.id"), nullable=True)
    delivery_date = Column(String, nullable=True)   # YYYY-MM-DD
    delivery_slot = Column(String, nullable=False)  # e.g. morning, afternoon, evening
    slot_start = Column(DateTime, nullable=True)
    slot_end = Column(DateTime, nullable=True)
    cutoff_time = Column(DateTime, nullable=True)
    min_threshold_kg = Column(Float, default=25.0)  # Configurable per zone / batch
    max_weight_kg = Column(Float, default=1000.0)   # Weight limit
    max_orders = Column(Integer, default=50)        # Order-count limit
    total_weight_kg = Column(Float, default=0.0)
    current_order_count = Column(Integer, default=0)
    status = Column(String, default="open")         # open | full | cutoff_reached | dispatched | completed | review_required
    below_threshold_action = Column(String, default="review_required")
    logistics_partner_id = Column(String, ForeignKey("logistics_partners.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="batch")
    zone = relationship("DeliveryZone", back_populates="batches")
    drop_point = relationship("SharedDropPoint", back_populates="batches")
    logistics_partner = relationship("LogisticsPartner")


class LogisticsPartner(Base):
    __tablename__ = "logistics_partners"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    vehicle_type = Column(SAEnum(VehicleType), nullable=False)
    capacity_kg = Column(Float, nullable=False)
    cost_per_km = Column(Float, nullable=False)
    base_cost = Column(Float, default=0.0)
    is_available = Column(Boolean, default=True)
    supports_cold_chain = Column(Boolean, default=False)
    current_location = Column(String, nullable=True)
    rating = Column(Float, default=4.5)


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"), unique=True, nullable=False)
    logistics_partner_id = Column(String, ForeignKey("logistics_partners.id"), nullable=True)
    delivery_mode = Column(String, default="home_delivery")
    drop_point_id = Column(String, ForeignKey("shared_drop_points.id"), nullable=True)
    distance_km = Column(Float, nullable=True)
    delivery_cost = Column(Float, nullable=True)
    otp = Column(String, nullable=True)  # Kept for backward compatibility
    receiver_confirmed = Column(Boolean, default=False)
    confirmed_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    delivery_attempt_logged = Column(Boolean, default=False)
    delivery_attempt_notes = Column(Text, nullable=True)
    status = Column(SAEnum(DeliveryStatus), default=DeliveryStatus.pending)
    route_sequence = Column(Text, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    order = relationship("Order", back_populates="delivery")
    logistics_partner = relationship("LogisticsPartner")
    confirmed_by = relationship("User", foreign_keys=[confirmed_by_id])
    drop_point = relationship("SharedDropPoint")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"), unique=True, nullable=False)
    total_amount = Column(Float, nullable=False)
    amount_paise = Column(Integer, default=0)
    platform_fee = Column(Float, nullable=False)
    platform_fee_paise = Column(Integer, default=0)
    logistics_share = Column(Float, nullable=False)
    logistics_share_paise = Column(Integer, default=0)
    farmer_share = Column(Float, nullable=False)
    farmer_share_paise = Column(Integer, default=0)
    refunded_amount_paise = Column(Integer, default=0)

    # Lifecycle & Gateway fields
    status = Column(String, default="pending")  # Matches PaymentStatus
    gateway_provider = Column(String, default="mock")  # mock | razorpay
    gateway_order_id = Column(String, nullable=True)
    gateway_payment_id = Column(String, nullable=True)
    gateway_signature = Column(String, nullable=True)
    gateway_status = Column(String, nullable=True)
    gateway_refund_id = Column(String, nullable=True)
    idempotency_key = Column(String, unique=True, nullable=True)

    is_on_hold = Column(Boolean, default=False)
    hold_reason = Column(String, nullable=True)
    buyer_confirmation_deadline = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    order = relationship("Order", back_populates="payment")
    ledger_entries = relationship("PaymentLedgerEntry", back_populates="payment", cascade="all, delete-orphan")


class PaymentLedgerEntry(Base):
    __tablename__ = "payment_ledger_entries"

    id = Column(String, primary_key=True, default=gen_uuid)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    amount_paise = Column(Integer, default=0)
    currency = Column(String, default="INR")
    actor_id = Column(String, nullable=True)
    actor_type = Column(String, default="system")  # system | buyer | admin | reviewer | gateway_webhook
    reason = Column(Text, nullable=False)
    gateway_reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    payment = relationship("Payment", back_populates="ledger_entries")
    order = relationship("Order")


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"), unique=True, nullable=False)
    buyer_id = Column(String, ForeignKey("buyer_profiles.id"), nullable=False)
    reason = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="OPEN")  # Matches DisputeStatus
    assigned_reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)
    resolution_decision = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    order = relationship("Order", back_populates="dispute")
    buyer = relationship("BuyerProfile")
    assigned_reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    evidence_items = relationship("DisputeEvidence", back_populates="dispute", cascade="all, delete-orphan")


class DisputeEvidence(Base):
    __tablename__ = "dispute_evidence"

    id = Column(String, primary_key=True, default=gen_uuid)
    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dispute = relationship("Dispute", back_populates="evidence_items")


class MandiPriceRecord(Base):
    __tablename__ = "mandi_price_records"

    id = Column(String, primary_key=True, default=gen_uuid)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    market = Column(String, nullable=False)
    commodity = Column(String, nullable=False, index=True)
    variety = Column(String, default="Common")
    arrival_date = Column(String, nullable=False)   # YYYY-MM-DD
    min_price = Column(Float, nullable=False)       # INR per Quintal
    max_price = Column(Float, nullable=False)
    modal_price = Column(Float, nullable=False)
    arrivals_ton = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
