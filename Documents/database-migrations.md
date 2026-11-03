# FarmCart — Database Schema & Migration Guide

**Author:** Swyam Shukla (Database Lead & API Integration Engineer 1)  
**ORM Framework:** SQLAlchemy 2.0 (Declarative Base)  
**Supported RDBMS:** SQLite (Local Dev) / PostgreSQL 16 (Production)  

---

## 1. Relational Entity Relationship (ER) Model

The FarmCart schema is structured around transactional integrity and strict foreign-key relationships:

```text
       ┌───────────────┐
       │     User      │
       └───────┬───────┘
               │ 1:1
       ┌───────┴───────┬──────────────────┐
       ▼                                  ▼
┌──────────────┐                  ┌──────────────┐
│FarmerProfile │                  │ BuyerProfile │
└──────┬───────┘                  └──────┬───────┘
       │ 1:N                             │ 1:N
       ▼                                 ▼
┌──────────────┐                  ┌──────────────┐
│   Produce    │                  │    Order     │◄─────────┐
└──────┬───────┘                  └──────┬───────┘          │
       │                                 │                  │
       │ 1:N                             │ 1:N              │
       │       ┌───────────────────┐     │                  │
       └──────>│    OrderItem      │<────┘                  │
               └───────────────────┘                        │
                                                            │
┌──────────────────┐           ┌──────────────────┐         │
│  DeliveryBatch   │           │ LogisticsPartner │         │
└────────┬─────────┘           └────────┬─────────┘         │
         │ 1:N                          │ 1:N               │
         └─────────────┬────────────────┘                   │
                       ▼                                    │
               ┌──────────────────┐                         │
               │     Delivery     │─────────────────────────┘
               └────────┬─────────┘
                        │ 1:1
                        ▼
               ┌──────────────────┐
               │     Payment      │
               └──────────────────┘

               ┌─────────────────────┐
               │  MandiPriceRecord   │ (Independent Market Analytics)
               └─────────────────────┘
```

---

## 2. Table Specifications

| Table Name | Primary Key | Foreign Keys | Key Indexes | Description |
|---|---|---|---|---|
| `users` | `id` (UUID str) | — | `email` (unique) | Core user authentication and credentials |
| `farmer_profiles` | `id` (UUID str) | `user_id` -> `users.id` | `user_id` (unique) | Farm or FPO name, pickup village, lat/long |
| `buyer_profiles` | `id` (UUID str) | `user_id` -> `users.id` | `user_id` (unique) | Buyer type (`individual` / `bulk`), delivery location |
| `produce` | `id` (UUID str) | `farmer_id` -> `farmer_profiles.id` | `farmer_id`, `status` | Listed inventory batches, pricing, quality grade |
| `orders` | `id` (UUID str) | `buyer_id`, `batch_id` | `buyer_id`, `batch_id`, `status` | Placed orders, delivery slots, total amount |
| `order_items` | `id` (UUID str) | `order_id`, `produce_id` | `order_id`, `produce_id` | Individual line items, quantities, subtotal |
| `delivery_batches`| `id` (UUID str) | `logistics_partner_id` | `area_key`, `delivery_slot` | Consolidated individual deliveries (>=25kg threshold) |
| `logistics_partners`| `id` (UUID str) | — | `vehicle_type`, `is_available` | Fleet registry: capacity, base cost, cost/km, cold chain |
| `deliveries` | `id` (UUID str) | `order_id`, `logistics_partner_id`| `order_id` (unique) | Dispatch tracking, calculated route, 6-digit OTP |
| `payments` | `id` (UUID str) | `order_id` -> `orders.id` | `order_id` (unique) | 3-way financial ledger: farmer share, logistics, fee |
| `mandi_price_records`| `id` (UUID str) | — | `commodity`, `arrival_date` | Official benchmark market prices from APMCs |

---

## 3. Dual Engine Compatibility Architecture

FarmCart supports both SQLite (for zero-dependency local runs) and PostgreSQL 16 (for production multi-container deployments):

- In `app/database.py`:
  ```python
  connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
  engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
  ```
- **SQLite Advantage**: Eliminates the requirement to run local PostgreSQL servers during early development or test discovery.
- **PostgreSQL Advantage**: Implements true ACID row-level locking and native enum support via `psycopg2-binary`.

---

## 4. Alembic Migration Procedure (Phase 2 Upgrade Plan)

To transition from `Base.metadata.create_all()` to formal version-controlled migrations:

### Step 1: Initialize Alembic
```bash
cd backend
alembic init alembic
```

### Step 2: Configure `alembic/env.py`
Connect Alembic to our SQLAlchemy models and settings:
```python
from app.database import Base
from app.config import settings
from app import models

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.database_url)
```

### Step 3: Generate Initial Migration
```bash
alembic revision --autogenerate -m "initial_schema_with_mandi_prices"
```

### Step 4: Apply Migrations
```bash
alembic upgrade head
```

---

## 5. Development Database Seeding

To populate initial accounts, fleet partners, produce items, and mandi benchmarks:
```bash
cd backend
python seed.py
```
This script verifies existing entities to avoid duplicate insertion and outputs test account credentials upon completion.
