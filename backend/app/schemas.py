"""
Pydantic Request & Response Validation Schemas
Primary Maintainer: Swyam Shukla (Database Lead)
Extended for Phase 2: Delivery Zones, Shared Drop Points, Serviceability,
5-State Order Tracking, Disputes, and Payment Gateways.
"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator

from .models import (
    UserRole,
    BuyerType,
    ProduceStatus,
    OrderType,
    OrderStatus,
    VehicleType,
    DeliveryStatus,
    DeliveryMode,
    DisputeStatus,
    DisputeReason,
    PaymentStatus,
)

# Indian PIN code validator pattern: exactly 6 digits, first digit 1-9
PINCODE_REGEX = re.compile(r"^[1-9][0-9]{5}$")


def validate_pincode_str(pincode: Optional[str]) -> Optional[str]:
    if pincode is None:
        return None
    val = str(pincode).strip()
    if not PINCODE_REGEX.match(val):
        raise ValueError("Invalid Indian PIN code. Must be exactly 6 numeric digits and cannot start with 0.")
    return val


# ---------- Auth / Users ----------

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6)
    role: UserRole

    # Farmer-specific attributes
    farm_or_fpo_name: Optional[str] = None
    pickup_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Buyer-specific attributes
    buyer_type: Optional[BuyerType] = None
    business_name: Optional[str] = None
    default_location: Optional[str] = None

    # Address attributes (Phase 2)
    address_line: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None

    @field_validator("pincode")
    @classmethod
    def check_pincode(cls, v):
        return validate_pincode_str(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    buyer_type: Optional[BuyerType] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Delivery Zones & Drop Points (Phase 2) ----------

class DeliveryZoneCreate(BaseModel):
    name: str
    state: str
    district: str
    city: Optional[str] = None
    serviceable_pincodes: List[str]
    is_active: bool = True
    min_batch_threshold_kg: float = Field(default=25.0, ge=0)
    max_batch_weight_kg: float = Field(default=1000.0, gt=0)
    max_batch_orders: int = Field(default=50, gt=0)
    preparation_buffer_hours: float = Field(default=4.0, ge=0)
    dispatch_buffer_hours: float = Field(default=2.0, ge=0)
    allows_home_delivery: bool = True
    allows_drop_point: bool = True

    @field_validator("serviceable_pincodes")
    @classmethod
    def validate_pincodes(cls, v):
        if not v:
            raise ValueError("Zone must specify at least one serviceable PIN code.")
        cleaned = []
        for p in v:
            p_str = validate_pincode_str(p)
            if p_str:
                cleaned.append(p_str)
        return cleaned


class DeliveryZoneUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    serviceable_pincodes: Optional[List[str]] = None
    is_active: Optional[bool] = None
    min_batch_threshold_kg: Optional[float] = None
    max_batch_weight_kg: Optional[float] = None
    max_batch_orders: Optional[int] = None
    preparation_buffer_hours: Optional[float] = None
    dispatch_buffer_hours: Optional[float] = None
    allows_home_delivery: Optional[bool] = None
    allows_drop_point: Optional[bool] = None


class DeliveryZoneOut(BaseModel):
    id: str
    name: str
    state: str
    district: str
    city: Optional[str] = None
    serviceable_pincodes: str
    is_active: bool
    min_batch_threshold_kg: float
    max_batch_weight_kg: float
    max_batch_orders: int
    preparation_buffer_hours: float
    dispatch_buffer_hours: float
    allows_home_delivery: bool
    allows_drop_point: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SharedDropPointCreate(BaseModel):
    zone_id: str
    name: str
    address_line: str
    locality: Optional[str] = None
    city: str
    district: str
    state: str
    pincode: str
    operating_hours: str = "08:00 - 20:00"
    contact_phone: Optional[str] = None
    capacity_orders: int = 100
    is_active: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("pincode")
    @classmethod
    def check_pincode(cls, v):
        return validate_pincode_str(v)


class SharedDropPointUpdate(BaseModel):
    name: Optional[str] = None
    address_line: Optional[str] = None
    locality: Optional[str] = None
    operating_hours: Optional[str] = None
    contact_phone: Optional[str] = None
    capacity_orders: Optional[int] = None
    is_active: Optional[bool] = None


class SharedDropPointOut(BaseModel):
    id: str
    zone_id: str
    name: str
    address_line: str
    locality: Optional[str] = None
    city: str
    district: str
    state: str
    pincode: str
    operating_hours: str
    contact_phone: Optional[str] = None
    capacity_orders: int
    is_active: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceabilityCheckRequest(BaseModel):
    pincode: str
    delivery_mode: Optional[DeliveryMode] = DeliveryMode.home_delivery
    order_weight_kg: Optional[float] = None

    @field_validator("pincode")
    @classmethod
    def check_pincode(cls, v):
        return validate_pincode_str(v)


class ServiceabilityCheckResponse(BaseModel):
    serviceable: bool
    pincode: str
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    allows_home_delivery: bool = False
    allows_drop_point: bool = False
    available_drop_points: List[SharedDropPointOut] = []
    available_slots: List[str] = ["morning", "afternoon", "evening"]
    reasons: List[str] = []


# ---------- Produce ----------

class ProduceCreate(BaseModel):
    product_name: str
    quantity_available: float = Field(gt=0)
    unit: str = "kg"
    quality_grade: str = "A"
    price_per_unit: float = Field(gt=0)
    available_date: Optional[datetime] = None
    pickup_location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ProduceOut(BaseModel):
    id: str
    farmer_id: str
    product_name: str
    quantity_available: float
    unit: str
    quality_grade: str
    price_per_unit: float
    available_date: datetime
    pickup_location: str
    status: ProduceStatus

    class Config:
        from_attributes = True


# ---------- Orders ----------

class OrderItemCreate(BaseModel):
    produce_id: str
    quantity: float = Field(gt=0)


class OrderCreate(BaseModel):
    order_type: OrderType
    delivery_mode: DeliveryMode = DeliveryMode.home_delivery
    delivery_location: str
    address_line: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    drop_point_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    delivery_slot: str  # Format: "YYYY-MM-DD|slot" or "YYYY-MM-DD|morning"
    items: List[OrderItemCreate]

    @field_validator("pincode")
    @classmethod
    def check_pincode(cls, v):
        if v is not None:
            return validate_pincode_str(v)
        return v


class OrderItemOut(BaseModel):
    id: str
    produce_id: str
    quantity: float
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class OrderStatusHistoryOut(BaseModel):
    id: str
    previous_status: Optional[str] = None
    new_status: str
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeliveryBatchOut(BaseModel):
    id: str
    zone_id: Optional[str] = None
    area_key: str
    delivery_mode: Optional[str] = "home_delivery"
    drop_point_id: Optional[str] = None
    delivery_date: Optional[str] = None
    delivery_slot: str
    slot_start: Optional[datetime] = None
    slot_end: Optional[datetime] = None
    cutoff_time: Optional[datetime] = None
    min_threshold_kg: Optional[float] = 25.0
    max_weight_kg: Optional[float] = 1000.0
    max_orders: Optional[int] = 50
    status: str
    total_weight_kg: float
    current_order_count: Optional[int] = 0

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: str
    buyer_id: str
    order_type: OrderType
    delivery_mode: Optional[str] = "home_delivery"
    delivery_location: str
    address_line: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    delivery_slot: str
    status: OrderStatus
    total_amount: float
    batch_id: Optional[str] = None
    zone_id: Optional[str] = None
    drop_point_id: Optional[str] = None
    batch: Optional[DeliveryBatchOut] = None
    drop_point: Optional[SharedDropPointOut] = None
    items: List[OrderItemOut] = []
    confirmed_at: Optional[datetime] = None
    processing_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    is_dispute_eligible: Optional[bool] = False
    created_at: datetime

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    reason: Optional[str] = None


class OrderTrackingOut(BaseModel):
    order_id: str
    current_status: OrderStatus
    delivery_mode: str
    delivery_slot: str
    delivery_location: str
    pincode: Optional[str] = None
    drop_point: Optional[SharedDropPointOut] = None
    batch: Optional[DeliveryBatchOut] = None
    status_history: List[OrderStatusHistoryOut] = []
    receiver_confirmation_pending: bool = False
    dispute_eligible: bool = False
    dispute_remaining_hours: Optional[float] = None


# ---------- Logistics ----------

class LogisticsPartnerCreate(BaseModel):
    name: str
    vehicle_type: VehicleType
    capacity_kg: float = Field(gt=0)
    cost_per_km: float = Field(ge=0)
    base_cost: float = Field(default=0.0, ge=0)
    supports_cold_chain: bool = False
    current_location: Optional[str] = None


class LogisticsPartnerOut(BaseModel):
    id: str
    name: str
    vehicle_type: VehicleType
    capacity_kg: float
    cost_per_km: float
    is_available: bool
    rating: float

    class Config:
        from_attributes = True


class DeliveryOut(BaseModel):
    id: str
    order_id: str
    logistics_partner_id: Optional[str] = None
    delivery_mode: Optional[str] = "home_delivery"
    drop_point_id: Optional[str] = None
    distance_km: Optional[float] = None
    delivery_cost: Optional[float] = None
    status: DeliveryStatus
    otp: Optional[str] = None  # Legacy support
    receiver_confirmed: bool = False
    confirmed_at: Optional[datetime] = None
    route_sequence: Optional[str] = None
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeliveryConfirm(BaseModel):
    otp: str


class ReceiverReceiptConfirm(BaseModel):
    notes: Optional[str] = None


# ---------- Disputes (Phase 2) ----------

class DisputeCreate(BaseModel):
    order_id: str
    reason: DisputeReason
    description: str = Field(min_length=10)


class DisputeResolution(BaseModel):
    decision: str  # "REFUND" | "RELEASE" | "REJECTED"
    notes: str = Field(min_length=5)


class DisputeEvidenceOut(BaseModel):
    id: str
    file_name: str
    mime_type: str
    file_size_bytes: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DisputeOut(BaseModel):
    id: str
    order_id: str
    buyer_id: str
    reason: str
    description: str
    status: str
    assigned_reviewer_id: Optional[str] = None
    resolution_decision: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_by_id: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    evidence_items: List[DisputeEvidenceOut] = []

    class Config:
        from_attributes = True


# ---------- Payments & Gateway (Phase 2) ----------

class PaymentInitiateRequest(BaseModel):
    provider: Optional[str] = None  # None uses configured default ("mock" or "razorpay")
    idempotency_key: Optional[str] = None


class PaymentInitiateResponse(BaseModel):
    payment_id: str
    order_id: str
    amount_inr: float
    amount_paise: int
    currency: str = "INR"
    gateway_provider: str
    gateway_order_id: str
    key_id: Optional[str] = None
    checkout_options: Dict[str, Any] = {}


class PaymentVerifyRequest(BaseModel):
    gateway_order_id: str
    gateway_payment_id: str
    gateway_signature: str


class PaymentVerifyResponse(BaseModel):
    verified: bool
    status: str
    payment_id: str
    message: str


class PaymentRefundRequest(BaseModel):
    amount_inr: Optional[float] = None
    reason: str = Field(min_length=5)


class PaymentLedgerEntryOut(BaseModel):
    id: str
    payment_id: str
    order_id: str
    previous_status: Optional[str] = None
    new_status: str
    amount: float
    currency: str
    actor_type: str
    reason: str
    gateway_reference: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    id: str
    order_id: str
    total_amount: float
    platform_fee: float
    logistics_share: float
    farmer_share: float
    status: str
    gateway_provider: Optional[str] = "mock"
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    gateway_status: Optional[str] = None
    is_on_hold: bool = False
    hold_reason: Optional[str] = None
    buyer_confirmation_deadline: Optional[datetime] = None
    settled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Mandi Benchmark Data ----------

class MandiPriceCreate(BaseModel):
    state: str
    district: str
    market: str
    commodity: str
    variety: str = "Common"
    arrival_date: str
    min_price: float
    max_price: float
    modal_price: float
    arrivals_ton: float = 0.0


class MandiPriceRecordOut(BaseModel):
    id: str
    state: str
    district: str
    market: str
    commodity: str
    variety: str
    arrival_date: str
    min_price: float
    max_price: float
    modal_price: float
    arrivals_ton: float

    class Config:
        from_attributes = True
