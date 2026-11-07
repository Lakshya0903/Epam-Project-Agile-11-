# FarmCart

**Direct Farm-to-Consumer Marketplace**

Full-stack reference platform connecting farmers and Farmer Producer Organizations (FPOs) directly with consumers, retailers, and bulk buyers.

```text
Farmer/FPO -> Register/Login -> Add Produce -> List on Platform
   -> Buyer Marketplace (bulk / individual)
   -> Place Order -> Save Order in DB -> Smart Order Engine
        (match inventory, check qty/location/time, calc demand)
   -> Bulk: direct order processing
      Individual: find nearby orders (same area + slot) -> batch (>=25kg) or
                  offer direct delivery for an extra cost
   -> Calculate Delivery Requirement -> Find Logistics Partners
      -> Smart Logistics Selection (cost, capacity, distance, availability)
      -> Select best/cheapest option -> Optimize pickup + delivery route
   -> Farmer/FPO pickup -> Optimized delivery route -> Product delivered
   -> Delivery confirmation (OTP) -> Payment settlement
      -> Farmer/FPO receives produce value
      -> Logistics partner payment
      -> Platform revenue
```

---

## 1. System Status & Feature Verification

To ensure engineering transparency, the table below documents the exact implementation status of each system component:

| Feature Component | Implementation Status | Implementation Details / Verification |
|---|:---:|---|
| **Farmer Registration & Profiles** | **Verified Implemented** | Full ORM persistence in `users` and `farmer_profiles` tables (`routers/auth.py`). |
| **Buyer Registration & Profiles** | **Verified Implemented** | Supports `individual` and `bulk` buyer types (`routers/auth.py`). |
| **Produce Catalog & Inventory** | **Verified Implemented** | Full CRUD, quantity reservation, auto status change to `sold_out` (`routers/produce.py`). |
| **Smart Order Engine** | **Verified Implemented** | Inventory checks, total amount calculation, bulk vs individual branching (`services/order_engine.py`). |
| **Smart Batching Engine** | **Verified Implemented** | Groups by normalized area key & delivery slot, 25 kg minimum threshold (`services/batch_engine.py`). |
| **Direct Delivery Opt-Out** | **Verified Implemented** | Allows individual buyer to exit batch queue for +25% delivery surcharge (`routers/orders.py`). |
| **Logistics Partner Selection** | **Verified Implemented** | Filter by vehicle capacity, cold-chain capability, cheapest cost + rating (`services/logistics_engine.py`). |
| **Route Optimization** | **Verified Implemented** | Nearest-neighbour heuristic visiting unique farmer pickups then buyer dropoffs. |
| **Delivery Confirmation & OTP** | **Verified Implemented** | 6-digit OTP generation, delivery verification endpoint (`services/payment_engine.py`). |
| **Payment Settlement** | **Verified Implemented** | Atomic ledger split: Farmer share, Logistics fee, Platform fee (`services/payment_engine.py`). |
| **Platform Revenue Dashboard** | **Verified Implemented** | Aggregated revenue query for admin role at `GET /platform/revenue` (`routers/payments.py`). |
| **Multilingual Frontend** | **Verified Implemented** | 10 Indian languages supported via `frontend/js/lang.js` dictionary without build tools. |
| **Real Geocoding / Routing API** | *Roadmap / Planned* | Currently uses Haversine formula with stable pseudo-distance fallback (`utils/geo.py`). |
| **Production Payment Gateway** | *Roadmap / Planned* | Currently uses internal ledger bookkeeping; external UPI/Razorpay integration planned for Phase 2. |
| **Live Agmarknet / Mandi API Sync**| *Roadmap / Planned* | Analytical modeling created; real-time scheduled scraping/API sync planned for Phase 2. |

---

## 2. Tech Stack

- **Backend**: Python 3.12+ / FastAPI / SQLAlchemy 2.0 / Pydantic v2
- **Database**: Dual compatibility: **SQLite** (zero-setup local dev) and **PostgreSQL 16** (production / Docker)
- **Authentication**: JWT (JSON Web Tokens) with passlib bcrypt password hashing
- **Frontend**: Vanilla HTML5, modern CSS3 (responsive grid/flexbox), Vanilla JavaScript (ES6 Modules, Fetch API, no build tools required)
- **Testing**: Python standard `unittest` test suite with `pytest` compatibility

---

## 3. Project Structure

```text
farmcart/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py            # User registration, login, JWT token issuance
│   │   │   ├── produce.py         # Produce listing and marketplace search
│   │   │   ├── orders.py          # Order placement, status, direct delivery toggle
│   │   │   ├── logistics.py       # Logistics partners pool & delivery confirmation
│   │   │   ├── payments.py        # Payment settlement records & admin revenue stats
│   │   │   └── analytics.py       # Mandi price benchmarks & trend queries
│   │   ├── services/
│   │   │   ├── order_engine.py    # Inventory validation & bulk/individual branching
│   │   │   ├── batch_engine.py    # Area & slot clustering, 25kg threshold logic
│   │   │   ├── logistics_engine.py# Vehicle selection & nearest-neighbour routing
│   │   │   ├── payment_engine.py  # OTP confirmation & 3-way split ledger
│   │   │   ├── produce_engine.py  # Produce business rules & query filtering
│   │   │   └── mandi_data_service.py # Historical mandi price database service
│   │   ├── utils/
│   │   │   ├── security.py        # Password hashing & JWT auth dependencies
│   │   │   ├── geo.py             # Haversine distance & pseudo-distance fallback
│   │   │   └── otp.py             # 6-digit random numeric OTP generation
│   │   ├── config.py              # Environment configuration via Pydantic Settings
│   │   ├── database.py            # Dual-mode engine (SQLite & PostgreSQL) & session
│   │   ├── main.py                # FastAPI app assembly, CORS, static frontend mount
│   │   ├── models.py              # SQLAlchemy ORM database models
│   │   └── schemas.py             # Pydantic validation schemas
│   ├── .env.example               # Environment variable blueprint
│   ├── Dockerfile                 # Container image specification
│   ├── requirements.txt           # Python dependency manifest
│   └── seed.py                    # Test users, vehicles, produce & mandi prices
├── frontend/
│   ├── index.html                 # Public portal: login, registration, hero
│   ├── dashboard.html             # Authenticated shell: Farmer, Buyer, Logistics, Admin
│   ├── analytics.html             # Market intelligence: mandi trends & price spread
│   ├── css/
│   │   └── style.css              # Unified design system & responsive styling
│   └── js/
│       ├── api.js                 # Central API request wrapper & session management
│       ├── auth.js                # Login & registration form event handlers
│       ├── dashboard.js           # Role-based dashboard logic & order lifecycle rails
│       ├── analytics.js           # Analytics chart visualizer & comparative tables
│       └── lang.js                # 10-language localization dictionary
├── tests/
│   ├── test_auth.py               # Authentication & token tests
│   ├── test_produce.py            # Produce CRUD & inventory tests
│   ├── test_orders.py             # Order engine & batching tests
│   ├── test_logistics.py          # Logistics partner selection & route tests
│   └── test_payments.py           # OTP & settlement split tests
├── analytics/
│   ├── mandi_analysis.py          # Price spread & moving average calculations
│   └── data_quality.py            # Mandi dataset validation & audit
├── ml/
│   ├── evaluation.py              # Evaluation metrics (MAE, RMSE, MAPE)
│   ├── price_predictor.py         # Agricultural price forecasting models
│   └── experiments/
│       ├── baseline_experiment.py # Benchmarking experiment runner
│       └── dataset_generator.py   # Synthetic seasonal mandi data generator
├── docs/
│   ├── project-overview.md        # Problem statement & scope
│   ├── architecture.md            # System architecture & data flow
│   ├── data-sources.md            # Indian mandi price API research
│   ├── test-report.md             # Quality assurance & test results
│   ├── analytics-report.md        # Price volatility & spread analysis
│   ├── database-migrations.md     # Schema migration & Alembic guide
│   └── ml-feasibility-report.md   # ML feasibility & ROI assessment
├── docker-compose.yml             # Postgres + API multi-container orchestration
└── .gitignore                     # Repository hygiene specification
```

---

## 4. Quickstart Guide

### Option A: Local Development with SQLite (Fastest — No external DB needed)

1. **Navigate to the backend directory and set up environment:**
   ```bash
   cd backend
   copy .env.example .env     # On Linux/macOS: cp .env.example .env
   ```
   *(By default, `.env` points to `sqlite:///./farmcart.db` for instant local execution).*

2. **Activate Python Virtual Environment & Install Dependencies:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate    # On Linux/macOS: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Seed Database with Test Accounts and Partners:**
   ```bash
   python seed.py
   ```

4. **Launch the FastAPI Server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Access the Application:**
   - **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Frontend Portal**: [http://localhost:8000/frontend/index.html](http://localhost:8000/frontend/index.html) or open `frontend/index.html` directly in any web browser.

---

### Option B: Docker Compose (Production-grade PostgreSQL)

```bash
# Build and run Postgres database + backend API
docker compose up --build

# In a separate terminal, seed demo data:
docker compose exec backend python seed.py
```

---

## 5. Seed Test Credentials

When `seed.py` is executed, the following pre-configured test accounts are available:

| Role | Email | Password | Pre-configured Data |
|---|---|---|---|
| **Farmer** | `farmer@test.com` | `Test123!` | Farm profile in Delhi, ready to list produce |
| **Buyer (Individual)** | `buyer@test.com` | `Test123!` | Individual household profile in Delhi |
| **Logistics Admin** | `logistics@test.com` | `Test123!` | 4 fleet vehicles (Truck, Mini Truck, Van, Bike) |

---

## 6. Running the Automated Test Suite

All tests use Python's built-in `unittest` runner. Run from the repository root:

```bash
# Run all test suites:
python -m unittest discover tests

# Or run individual test modules:
python -m unittest tests.test_auth
python -m unittest tests.test_produce
python -m unittest tests.test_orders
python -m unittest tests.test_logistics
python -m unittest tests.test_payments
```

---

## 7. Quality Assurance & Phase 1 Team Deliverables

For the full 11-member team work breakdown, file ownership map, and PR instructions, consult:
- [`Phase 1/README.md`](file:///f:/Work-neimar/farm2market/Farm2Market/Phase%201/README.md)
- [`Phase 1/TEAM_FILE_MAP.md`](file:///f:/Work-neimar/farm2market/Farm2Market/Phase%201/TEAM_FILE_MAP.md)
