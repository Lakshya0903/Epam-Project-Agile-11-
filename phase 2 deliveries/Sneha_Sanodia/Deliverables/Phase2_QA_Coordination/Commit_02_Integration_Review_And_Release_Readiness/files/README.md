# FarmCart

**Direct Farm-to-Consumer Marketplace — Phase 2 Verified Implementation**

Full-stack reference platform connecting farmers and Farmer Producer Organizations (FPOs) directly with consumers, retailers, and bulk buyers.

```text
Farmer/FPO -> Register/Login -> Add Produce -> List on Platform
   -> Buyer Marketplace (bulk / individual)
   -> Nationwide Serviceability & PIN-Code Check (Delivery Zones & Shared Drop Points)
   -> Place Order -> Save Order in DB -> Smart Order Engine (Inventory checks, 5-state lifecycle)
   -> Smart Batching Engine (Dual Capacity: Weight kg & Order Count, Schedule Cutoff)
   -> Smart Logistics Selection & Route Optimization (Cold-chain, Capacity, Cost)
   -> Delivery Dispatch (Home Delivery / Shared Drop Point Hub)
   -> Receiver Confirmation Without OTP (Authenticated buyer receipt)
   -> 24-Hour Dispute Window & Protection Hold (Evidence upload & Reviewer workflow)
   -> Payment Gateway & Settlement (Double-entry Paise Ledger & Escrow Release)
```

---

## 1. System Status & Feature Verification

To ensure engineering transparency, the table below documents the exact implementation status of each system component:

| Feature Component | Implementation Status | Implementation Details / Verification |
|---|:---:|---|
| **Farmer Registration & Profiles** | **Verified Implemented** | Full ORM persistence in `users` and `farmer_profiles` tables (`routers/auth.py`). |
| **Buyer Registration & Profiles** | **Verified Implemented** | Supports `individual` and `bulk` buyer types with address fields (`routers/auth.py`). |
| **Produce Catalog & Inventory** | **Verified Implemented** | Full CRUD, quantity reservation, auto status change to `sold_out` (`routers/produce.py`). |
| **Nationwide Delivery Serviceability** | **Verified Implemented** | 6-digit Indian PIN-code validation (`^[1-9][0-9]{5}$`), `DeliveryZone` and `SharedDropPoint` routing (`services/serviceability_engine.py`). |
| **Automatic Delivery-Batch Engine** | **Verified Implemented** | Dual capacity enforcement (weight & order count), schedule cutoffs, drop point isolation, configurable minimum thresholds (`services/batch_engine.py`). |
| **Canonical 5-State Order Lifecycle** | **Verified Implemented** | Canonical state machine: `PLACED` -> `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED`, audited in `order_status_history` (`services/order_engine.py`). |
| **Delivery Confirmation Without OTP** | **Verified Implemented** | Authenticated receiver confirms delivery receipt without OTP, initiating the 24-hour buyer protection window (`services/payment_engine.py`). |
| **Dispute Management Subsystem** | **Verified Implemented** | 24-hour delivery dispute window, private photo evidence upload (JPEG/PNG/WebP, max 5MB), reviewer resolution workflow (`services/dispute_engine.py`). |
| **Payment Gateway Integration** | **Verified Implemented** | Clean provider abstraction (`BasePaymentGateway`, `MockPaymentGateway`, `RazorpayGateway`), HMAC-SHA256 signature verification (`services/payment_gateways/`). |
| **Payment Protection & Escrow Ledger** | **Verified Implemented** | Integer paise financial math, double-entry immutable audit trail (`payment_ledger_entries`), 24-hour confirmation hold before payout release (`services/payment_engine.py`). |
| **Four Operational Dashboards** | **Verified Implemented** | Dedicated interactive views for Buyer, Farmer, Logistics, and Admin/Reviewer connected to live backend APIs (`frontend/dashboard.html` & `frontend/js/dashboard.js`). |
| **Database Migrations (Alembic)** | **Verified Implemented** | Complete Alembic migration setup with SQLite batch mode support (`render_as_batch=True`) and PostgreSQL DDL compatibility (`backend/alembic/`). |
| **Direct Delivery Opt-Out** | **Verified Implemented** | Allows individual buyer to exit batch queue for +25% delivery surcharge (`routers/orders.py`). |
| **Logistics Partner Selection** | **Verified Implemented** | Filter by vehicle capacity, cold-chain capability, cheapest cost + rating (`services/logistics_engine.py`). |
| **Route Optimization** | **Verified Implemented** | Nearest-neighbour heuristic visiting unique farmer pickups then buyer dropoffs. |
| **Multilingual Frontend** | **Verified Implemented** | 10 Indian languages supported via `frontend/js/lang.js` dictionary without build tools. |
| **Analytics & Mandi Intelligence** | **Verified Implemented** | Agmarknet price benchmarks, price spread, and seasonal forecasting models (`analytics/` & `ml/`). |

---

## 2. Tech Stack

- **Backend**: Python 3.12+ / FastAPI / SQLAlchemy 2.0 / Pydantic v2
- **Database**: Dual compatibility: **SQLite** (zero-setup local dev) and **PostgreSQL 16** (production / Docker)
- **Database Migrations**: Alembic with batch mode support
- **Authentication**: JWT (JSON Web Tokens) with passlib bcrypt password hashing
- **Frontend**: Vanilla HTML5, modern CSS3 (responsive grid/flexbox), Vanilla JavaScript (ES6 Modules, Fetch API, no build tools required)
- **Payment Gateways**: Pluggable abstraction supporting Mock (offline test/dev) and Razorpay (sandbox/live)
- **Testing**: Python standard `unittest` test suite with 50 passing automated tests

---

## 3. Project Structure

```text
farmcart/
├── backend/
│   ├── alembic/                   # Alembic database migration scripts & env
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py            # User registration, login, JWT token issuance
│   │   │   ├── produce.py         # Produce listing and marketplace search
│   │   │   ├── orders.py          # Order placement, tracking, lifecycle transitions
│   │   │   ├── logistics.py       # Zones, drop points, serviceability, batches, fleet
│   │   │   ├── payments.py        # Gateway initiate, verify, webhooks, escrow ledger
│   │   │   ├── disputes.py        # Dispute filing, photo upload, reviewer resolution
│   │   │   └── analytics.py       # Mandi price benchmarks & trend queries
│   │   ├── services/
│   │   │   ├── order_engine.py    # 5-state lifecycle engine, validation, cancellation
│   │   │   ├── batch_engine.py    # Dual-capacity batch engine, cutoffs, drop points
│   │   │   ├── serviceability_engine.py # Indian PIN validator & zone lookup
│   │   │   ├── dispute_engine.py  # 24h dispute window, photo evidence, reviewer actions
│   │   │   ├── logistics_engine.py# Vehicle selection & nearest-neighbour routing
│   │   │   ├── payment_engine.py  # Gateway transactions, receiver confirm, paise ledger
│   │   │   ├── payment_gateways/  # Base, Mock, and Razorpay gateway providers
│   │   │   ├── produce_engine.py  # Produce business rules & query filtering
│   │   │   └── mandi_data_service.py # Historical mandi price database service
│   │   ├── utils/
│   │   │   ├── security.py        # Password hashing & JWT auth dependencies
│   │   │   ├── geo.py             # Indian PIN validation, Haversine & distance math
│   │   │   └── otp.py             # 6-digit random numeric OTP generation (legacy)
│   │   ├── config.py              # Environment configuration via Pydantic Settings
│   │   ├── database.py            # Dual-mode engine (SQLite & PostgreSQL) & session
│   │   ├── main.py                # FastAPI app assembly, CORS, static frontend mount
│   │   ├── models.py              # SQLAlchemy ORM database models
│   │   └── schemas.py             # Pydantic validation schemas
│   ├── .env.example               # Environment variable blueprint
│   ├── alembic.ini                # Alembic migration configuration
│   ├── Dockerfile                 # Container image specification
│   ├── requirements.txt           # Python dependency manifest
│   └── seed.py                    # Test users, vehicles, zones, drop points & produce
├── frontend/
│   ├── index.html                 # Public portal: login, registration, hero
│   ├── dashboard.html             # Shell: Farmer, Buyer, Logistics, and Admin Dashboards
│   ├── analytics.html             # Market intelligence: mandi trends & price spread
│   ├── css/
│   │   └── style.css              # Unified design system & responsive styling
│   └── js/
│       ├── api.js                 # Central API request wrapper, multipart & session
│       ├── auth.js                # Login & registration form event handlers
│       ├── dashboard.js           # Interactive controller: 4 dashboards & lifecycle rails
│       ├── analytics.js           # Analytics chart visualizer & comparative tables
│       └── lang.js                # 10-language localization dictionary
├── tests/
│   ├── test_auth.py               # Authentication & token tests
│   ├── test_produce.py            # Produce CRUD & inventory tests
│   ├── test_orders.py             # Order engine & batching tests
│   ├── test_logistics.py          # Logistics partner selection & route tests
│   ├── test_payments.py           # Legacy payment settlement & OTP tests
│   ├── test_serviceability_phase2.py # Nationwide PIN-code validation & zones
│   ├── test_batches_phase2.py     # Dual capacity, cutoffs & drop-point isolation
│   ├── test_delivery_confirmation_phase2.py # Receiver confirmation without OTP
│   ├── test_disputes_phase2.py    # 24h dispute window, photo evidence & hold
│   ├── test_payment_gateway_phase2.py # Gateway abstraction, signatures & ledger
│   └── test_phase2_workflows.py   # Complete end-to-end integration workflows
├── docs/                          # Comprehensive architectural and verification documentation
├── docker-compose.yml             # Postgres + API multi-container orchestration
└── .gitignore                     # Repository hygiene specification
```

---

## 4. Quickstart Guide

### Option A: Local Development with SQLite (Fastest — Zero Setup)

1. **Navigate to the backend directory and set up environment:**
   ```bash
   cd backend
   copy .env.example .env     # On Linux/macOS: cp .env.example .env
   ```

2. **Activate Python Virtual Environment & Install Dependencies:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate    # On Linux/macOS: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run Database Migrations & Seed Sample Data:**
   ```bash
   alembic upgrade head
   python seed.py
   ```

4. **Launch the FastAPI Server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Open your browser to:
   - **Frontend Application**: `http://localhost:8000/static/index.html`
   - **Interactive API Docs (Swagger UI)**: `http://localhost:8000/docs`
   - **Alternative ReDoc**: `http://localhost:8000/redoc`

---

## 5. Running Automated Tests

Run the complete 50-test automated test suite:
```bash
python -m unittest discover tests
```
All 50 unit, integration, and end-to-end workflow tests execute in ~14 seconds and verify:
- Indian PIN-code validation and delivery serviceability
- Dual capacity batch allocation and schedule cutoffs
- Canonical 5-state lifecycle state machine
- Receiver confirmation without OTP
- Dispute filing, private photo upload, and reviewer refund/release
- Payment gateway initiation, HMAC-SHA256 signature verification, and integer paise ledger
- Full end-to-end customer lifecycles
