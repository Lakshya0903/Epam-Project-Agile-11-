# FarmCart Phase 2 — Baseline Repository Audit & Verification Report

**Author:** Agile 11 Architecture & Engineering Team  
**Date:** November 2026  
**Status:** Baseline Completed  

---

## 1. Existing Phase 1 Functionality
The repository contains a functional reference implementation for a Direct Farm-to-Consumer Marketplace with the following working subsystems:
- **Authentication & RBAC:** JWT authentication with HS256 signatures, `passlib` bcrypt hashing, and role-based checks for `farmer`, `buyer`, `logistics`, and `admin`.
- **Produce Catalog & Inventory:** Farmer harvest listings with price, quantity, grade, location, and automatic status transition to `sold_out` upon inventory exhaustion.
- **Smart Order Engine:** Atomic stock reservation, total calculations, and branching to bulk direct logistics vs. individual batching.
- **Smart Batching Engine:** Geographic clustering by delivery slot and coarse area key, enforcing a hardcoded 25 kg threshold and a 50 km farmer pickup compatibility radius.
- **Direct Delivery Opt-Out:** Allows individual buyers in open batches to exit the batch queue for a +25% freight surcharge.
- **Smart Logistics & Fleet Selection:** Vehicle matching across trucks, mini-trucks, vans, and bikes based on weight and cold-chain requirements, with a nearest-neighbour multi-stop routing heuristic.
- **Delivery Confirmation & OTP:** 6-digit numeric OTP generation and delivery verification endpoint.
- **Payment Settlement Ledger:** 3-way internal accounting split (Farmer share: 92%, Platform fee: 8% + 15% logistics markup, Logistics share: freight cost).
- **Frontend Experience:** Vanilla HTML5/CSS3/ES6 JavaScript frontend with role-specific views and 10 Indian language localizations (`lang.js`).
- **Analytics & Market Intelligence:** APMC mandi data quality auditing (`data_quality.py`) and price trend analysis (`mandi_analysis.py`).
- **Machine Learning Track:** Pure-Python forecasting evaluation framework comparing against a Naive Persistence baseline.

---

## 2. Existing Models & Database Relationships
The database layer (`backend/app/models.py`) defines 10 core SQLAlchemy models:
1. `User` (1:1 with `FarmerProfile`, 1:1 with `BuyerProfile`)
2. `FarmerProfile` (1:N with `Produce`)
3. `BuyerProfile` (1:N with `Order`)
4. `Produce` (1:N with `OrderItem`)
5. `Order` (1:N with `OrderItem`, N:1 with `DeliveryBatch`, 1:1 with `Delivery`, 1:1 with `Payment`)
6. `OrderItem` (N:1 with `Order`, N:1 with `Produce`)
7. `DeliveryBatch` (1:N with `Order`, N:1 with `LogisticsPartner`)
8. `LogisticsPartner` (1:N with `Delivery`, 1:N with `DeliveryBatch`)
9. `Delivery` (1:1 with `Order`, N:1 with `LogisticsPartner`)
10. `Payment` (1:1 with `Order`)
11. `MandiPriceRecord` (standalone analytics entity)

---

## 3. Existing API Endpoints
- **Auth (`/auth`):** `POST /register`, `POST /login`, `GET /me`
- **Produce (`/produce`):** `POST /`, `GET /`, `GET /mine`, `GET /{produce_id}`
- **Orders (`/orders`):** `POST /`, `GET /mine`, `GET /logistics`, `GET /{order_id}`, `POST /{order_id}/request-direct-delivery`
- **Logistics (`/`):** `POST /logistics-partners`, `GET /logistics-partners`, `GET /orders/{order_id}/delivery`, `POST /orders/{order_id}/confirm-delivery`
- **Payments (`/`):** `GET /orders/{order_id}/payment`, `GET /platform/revenue`
- **Analytics (`/analytics`):** `GET /mandi-prices`, `GET /summary/{commodity}`, `POST /mandi-prices`

---

## 4. Existing Frontend Capabilities
- `frontend/index.html`: Landing hero, login/register tabs with dynamic role inputs, helpline agent request.
- `frontend/dashboard.html`: Authenticated shell supporting Farmer, Buyer, Logistics, and Admin tabs. Order tracking includes a 6-stage lifecycle rail (`Placed` -> `Matched` -> `Batched` -> `Out for delivery` -> `Delivered` -> `Paid`), batch capacity progress bar, direct delivery toggle, and OTP confirmation.
- `frontend/analytics.html`: Wholesale mandi price benchmarks, commodity switcher, 7-day moving averages, spread calculator, and SVG chart visualizer.
- `frontend/js/api.js`: Centralized fetch wrapper handling session management and environment URLs.
- `frontend/js/lang.js`: 10-language localization dictionary (en, hi, mr, ta, te, bn, gu, kn, ml, pa).

---

## 5. Existing Tests & Baseline Results
Ran `python -m unittest discover tests` on repository baseline:
- Total tests executed: 18
- Passed: 17
- Failed: 1 (`test_double_confirmation_rejection` in `tests/test_payments.py`)
- Warning: `DeprecationWarning: datetime.datetime.utcnow()` in `tests/test_produce.py`.

---

## 6. Missing Phase 2 Functionality
1. **Nationwide Address & Serviceability:**
   - Formal Indian PIN code (6-digit) and address breakdown (PIN code, locality, city, district, state).
   - `DeliveryZone` and `SharedDropPoint` models with active/inactive management.
   - Server-side serviceability evaluation service and API (`/logistics/serviceability`).
2. **Advanced Automatic Delivery-Batch Engine:**
   - Auto-generation of batches by Zone/Area, Delivery Mode, Date, Slot, and Drop Point.
   - Dual capacity enforcement: Maximum weight (kg) AND Maximum order count.
   - Configurable minimum batch threshold replacing hardcoded 25 kg.
   - Schedule-driven cutoff calculation with preparation and dispatch buffers.
   - Deterministic automatic best-batch assignment without buyer manual selection.
   - Below-threshold cutoff administrative review and operational policies.
3. **Approved 5-State Order Lifecycle:**
   - Strict canonical states: `PLACED` -> `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED`.
   - Centralized state transition validator with actor permission checks and transition audit logs.
   - Order progress and tracking API returning batch, delivery mode, drop point, and dispute eligibility.
4. **Receiver Delivery Confirmation Without OTP:**
   - Receiver-authenticated confirmation without requiring a 6-digit OTP.
   - Delivery timestamp recording, 24-hour dispute window initialization, and separate payment release trigger.
5. **Dispute Management Subsystem:**
   - `Dispute` and `DisputeEvidence` models, repository routes (`/disputes`), and `dispute_engine.py`.
   - 24-hour post-delivery submission window enforcement.
   - Secure photographic and written evidence storage with private access controls.
   - Reviewer & admin resolution workflows.
   - Automatic payment hold on dispute submission.
6. **Payment Protection & Gateway Integration:**
   - Financial lifecycle state machine separated from order and delivery states.
   - Decimal/paise-safe append-only ledger entries (`PaymentLedgerEntry`).
   - Payment gateway abstraction (`BasePaymentGateway`, `MockPaymentGateway`, and `RazorpayGateway` adapter).
   - Configurable buyer confirmation period before payment release eligibility.
   - Dispute hold and refund processing.
7. **Four Dashboard Extensions:**
   - Buyer: Delivery mode selection (Home vs. Shared Drop Point), PIN validation, 5-state tracking, receiver confirmation button, 24-hour dispute form with photo upload.
   - Farmer: Incoming orders, batch allocation view, order fulfilment progress, dispute alerts.
   - Logistics: Assigned batches, drop point vs home route manifests, dispatch status, delivery attempt logging.
   - Admin: Zone & drop point configuration, batch monitoring/overrides, dispute resolution panel, payment ledger & gateway monitoring.
8. **Database Migrations:**
   - Alembic migration environment and versioned schema revisions.

---

## 7. Existing Defects Identified in Baseline
1. **`tests/test_payments.py` Test Failure:**
   - Cause: `confirm_delivery` raises `HTTPException(400, "Delivery has already been confirmed for this order")`. The test asserts `self.assertIn("already confirmed", ctx.exception.detail)`. The text has `"already been confirmed"`, missing the exact substring `"already confirmed"`.
2. **Missing `frontend/js/auth.js`:**
   - `frontend/index.html` references `<script src="js/auth.js"></script>`, but the file is absent on disk, preventing login/registration form submission and role tab switching on the landing page.
3. **Deprecated `datetime.utcnow()`:**
   - Multiple models and tests use deprecated `datetime.utcnow()` instead of timezone-aware UTC `datetime.now(timezone.utc)`.

---

## 8. Files Requiring Modification
- `backend/app/models.py`: Add delivery zones, drop points, order state transitions, dispute entities, payment ledger entries, gateway transaction fields.
- `backend/app/schemas.py`: Add Pydantic schemas for zones, drop points, serviceability, disputes, gateways, and lifecycle updates.
- `backend/app/config.py`: Add settings for payment gateways, dispute windows, confirmation buffers, upload limits.
- `backend/app/services/order_engine.py`: Integrate 5-state lifecycle validation, serviceability checks, and automatic batching.
- `backend/app/services/batch_engine.py`: Implement dual capacity (weight & order count), schedule-based cutoffs, configurable minimum thresholds.
- `backend/app/services/logistics_engine.py`: Support drop points, home delivery separation, receiver confirmation without OTP.
- `backend/app/services/payment_engine.py`: Integrate payment gateway abstraction, separate financial states, buyer confirmation period, and dispute holds.
- `backend/app/routers/orders.py`: Update order lifecycle, tracking, and cancellation endpoints.
- `backend/app/routers/logistics.py`: Add zone, drop point, serviceability, and receiver confirmation endpoints.
- `backend/app/routers/payments.py`: Add initiation, verification, webhook, ledger, and refund endpoints.
- `frontend/index.html`: Fix script reference and ensure robust auth form event handling.
- `frontend/dashboard.html` & `frontend/js/dashboard.js`: Expand Buyer, Farmer, Logistics, and Admin tabs for Phase 2 workflows.
- `frontend/js/lang.js`: Add i18n keys for Phase 2 UI strings.
- `backend/seed.py`: Seed Indian zones, drop points, and Phase 2 configurations.
- `backend/.env.example`: Add Phase 2 environment variables.
- `README.md`: Update feature matrix, documentation, and Phase 2 run instructions.

---

## 9. Proposed New Files
- `backend/app/services/dispute_engine.py`: Core dispute validation, evidence handling, and resolution logic.
- `backend/app/routers/disputes.py`: REST endpoints for dispute submission, evidence access, and review.
- `backend/app/services/payment_gateways/base.py`: Provider-neutral payment gateway interface.
- `backend/app/services/payment_gateways/mock_provider.py`: Deterministic mock payment gateway for testing and offline sandbox simulation.
- `backend/app/services/payment_gateways/razorpay_provider.py`: Razorpay payment gateway adapter (HMAC-SHA256 signature verification, order creation, refund API).
- `frontend/js/auth.js`: Missing client-side auth controller for login/registration forms and role field toggles.
- `alembic.ini` & `backend/migrations/`: Alembic database migration environment and versioned scripts.
- `tests/test_batches_phase2.py`: Automated tests for automatic batching, dual capacity, cutoffs, and thresholds.
- `tests/test_serviceability_phase2.py`: Automated tests for PIN codes, delivery zones, and drop points.
- `tests/test_delivery_confirmation_phase2.py`: Automated tests for receiver confirmation without OTP.
- `tests/test_disputes_phase2.py`: Automated tests for dispute submission, evidence privacy, payment holds, and resolutions.
- `tests/test_payment_gateway_phase2.py`: Automated tests for gateway initiation, verification, webhooks, and ledger.
- `tests/test_phase2_workflows.py`: End-to-end integration tests for Home Delivery, Shared Drop Point, and Dispute lifecycles.
- `docs/phase-2-*.md`: Architectural, database, API, payment gateway, security, operations, and completion documentation.

---

## 10. Technical Risks & Dependencies
1. **Dual DB Compatibility (SQLite vs PostgreSQL):** SQLite does not natively support `ALTER TABLE ... ADD CONSTRAINT` or certain enum types; migrations must use batch mode (`render_as_batch=True`).
2. **Concurrency in Batch Capacity:** Simultaneous checkout requests could overfill batch weight or order count limits; requires atomic reservation within transactions.
3. **Payment Gateway Credentials:** Live gateway accounts require registered Indian merchant entities; Phase 2 must provide full sandbox support with mock and Razorpay adapters while documenting live requirements.
4. **Dispute Photo Upload Security:** File upload attacks (path traversal, arbitrary code execution) must be mitigated with strict MIME/extension whitelisting, UUID renaming, and private non-executable storage.

