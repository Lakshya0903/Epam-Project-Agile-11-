# FarmCart — System Architecture & Technical Design

## 1. Architectural Overview

FarmCart is constructed as a decoupled, modular service-oriented web architecture:

- **Client Layer**: Vanilla HTML5, modern CSS3 with custom properties, and modular JavaScript (ES6+). Zero build tools required; runs natively in modern browsers or through static file serving.
- **Application Server**: **FastAPI** (Python 3.12+), providing asynchronous high-performance REST APIs, automatic OpenAPI/Swagger documentation, and Pydantic v2 data validation.
- **Data Persistence Layer**: **SQLAlchemy 2.0 ORM** supporting dual backends:
  - **SQLite**: Local zero-dependency development (`farmcart.db`).
  - **PostgreSQL 16**: Containerized production environment with connection pooling (`pool_pre_ping=True`).
- **Security & Identity**: JSON Web Tokens (JWT) using `python-jose` with HS256 signatures and Passlib bcrypt password hashing.

---

## 2. End-to-End System Block Diagram

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER (BROWSER)                          │
│                                                                        │
│   ┌────────────────────┐   ┌───────────────────┐   ┌───────────────┐   │
│   │ index.html (Auth)  │   │ dashboard.html    │   │ analytics.html│   │
│   └─────────┬──────────┘   └─────────┬─────────┘   └───────┬───────┘   │
│             │                        │                     │           │
│             └────────────────────────┴─────────────────────┘           │
│                                      │                                 │
│                              frontend/js/api.js                        │
│                         (Bearer Token + Fetch API)                     │
└──────────────────────────────────────┬─────────────────────────────────┘
                                       │ HTTP / REST
                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION SERVER                        │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                       ROUTER LAYER                             │   │
│   │   auth.py   |   produce.py   |   orders.py   |   logistics.py  │   │
│   │               payments.py    |   analytics.py                  │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                   │
│   ┌────────────────────────────────┴───────────────────────────────┐   │
│   │                      BUSINESS SERVICE ENGINES                  │   │
│   │                                                                │   │
│   │   ┌─────────────────────┐          ┌───────────────────────┐   │   │
│   │   │   order_engine.py   │◄─────────┤   batch_engine.py     │   │   │
│   │   │ (Stock Reserve &    │          │ (Area Clust, 25kg Min,│   │   │
│   │   │  Demand Calc)       │          │  Direct Opt-Out)      │   │   │
│   │   └──────────┬──────────┘          └───────────┬───────────┘   │   │
│   │              │                                 │               │   │
│   │              ▼                                 ▼               │   │
│   │   ┌─────────────────────┐          ┌───────────────────────┐   │   │
│   │   │ logistics_engine.py │          │   payment_engine.py   │   │   │
│   │   │ (Partner Selection, │          │ (OTP Verification &   │   │   │
│   │   │  Nearest-Neighbour) │          │  3-Way Settlement)    │   │   │
│   │   └─────────────────────┘          └───────────────────────┘   │   │
│   │                                                                │   │
│   │   ┌─────────────────────┐          ┌───────────────────────┐   │   │
│   │   │  produce_engine.py  │          │ mandi_data_service.py │   │   │
│   │   │ (Catalog Validation)│          │ (Price Persistence)   │   │   │
│   │   └─────────────────────┘          └───────────────────────┘   │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                   │
│   ┌────────────────────────────────┴───────────────────────────────┐   │
│   │                       UTILITY LAYER                            │   │
│   │      security.py (JWT/Bcrypt)   |   geo.py (Haversine)         │   │
│   │                      otp.py (6-Digit Gen)                      │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
└────────────────────────────────────┼───────────────────────────────────┘
                                     │ SQLAlchemy ORM
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        RELATIONAL DATABASE                             │
│                                                                        │
│   users               farmer_profiles     buyer_profiles               │
│   produce             orders              order_items                  │
│   delivery_batches    logistics_partners  deliveries                   │
│   payments            mandi_price_records                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Engine Mechanics

### 3.1 Smart Order Engine (`order_engine.py`)
1. **Atomic Stock Check**: Inspects requested quantities against `produce.quantity_available`.
2. **Immediate Deduction**: Deducts reserved quantities immediately. If remaining stock hits zero, status updates to `sold_out`.
3. **Branching**:
   - `bulk`: Direct order. Dispatches immediately to `logistics_engine.assign_logistics_for_order`.
   - `individual`: Dispatches to `batch_engine.try_batch_individual_order`.

### 3.2 Smart Batching Engine (`batch_engine.py`)
1. **Clustering Criteria**: Groups orders sharing the same `area_key` (normalized delivery locality) and `delivery_slot`.
2. **Farmer Pickup Compatibility**: Verifies that farmer pickup locations for batched orders lie within `MAX_PICKUP_DISTANCE_KM` (50 km).
3. **Dispatch Threshold**: Once batch reaches `MIN_BATCH_WEIGHT_KG` (25.0 kg), the batch is marked full and handed to the logistics engine.
4. **Direct Delivery Override**: If a buyer opts out (`request_direct_delivery`), their order is detached from the batch, weight is updated, and direct dispatch is triggered with a 25% delivery cost surcharge.

### 3.3 Logistics Engine (`logistics_engine.py`)
1. **Partner Matching**: Queries available partners matching required payload weight and cold-chain flag (`supports_cold_chain=True` for dairy, poultry, seafood).
2. **Cost Ranking**: Evaluates candidates by `total_cost = base_cost + cost_per_km * distance_km`, breaking ties by partner rating.
3. **Route Optimization**:
   - Collects unique farmer pickup points and sorts them via nearest-neighbour heuristic.
   - Visits all farmer points, then sequences buyer dropoff points nearest to last pickup.
   - Computes proportional freight cost per order based on weight share.

### 3.4 Payment Engine (`payment_engine.py`)
1. **OTP Verification**: Verifies buyer's 6-digit OTP against `delivery.otp`.
2. **State Transition**: Marks `delivery.status = delivered` and `order.status = paid`.
3. **Three-Way Ledger Split**:
   - **Farmer Share**: `total_amount - (total_amount * platform_fee_percent / 100)`
   - **Logistics Share**: `delivery_cost`
   - **Platform Revenue**: `(total_amount * platform_fee_percent / 100) + (delivery_cost * logistics_share_percent / 100)`
