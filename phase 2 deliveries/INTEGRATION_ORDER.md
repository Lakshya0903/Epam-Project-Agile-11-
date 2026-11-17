# FarmCart Phase 2 — Step-by-Step Branch Integration Order

To prevent git merge conflicts and ensure CI test suites never fail during PR merges, branches must be integrated into `main` in the following strict **6-wave sequence**:

---

### Wave 1: Architectural Baseline & Environment Foundation
*PR Merge Order:*
1. **Branch:** `feature/phase2-sneha-qa` (Sneha Sanodia — Commit 01)
   - Baseline audit, security review, and architecture document.
2. **Branch:** `feature/phase2-anshika-deployment` (Anshika Sharma — Commit 01)
   - Configuration baseline, `.env.example`, dependencies in `requirements.txt`.

---

### Wave 2: Persistence Layer & Data Contracts
*PR Merge Order:*
3. **Branch:** `feature/phase2-swyam-database` (Swyam Shukla — Commits 01, 02, 03)
   - SQLAlchemy Declarative models (`models.py`).
   - Pydantic v2 schemas (`schemas.py`) and API contracts (`phase-2-api-contracts.md`).
   - Alembic batch migration `22f82a866cc9` and seed data (`seed.py`).

---

### Wave 3: Core Domain Services & Logistics Engines
*PR Merge Order:*
4. **Branch:** `feature/phase2-yash-serviceability` (Yash Goyal — Commits 01, 02)
   - 6-digit Indian PIN code validator & serviceability engine (`geo.py`, `serviceability_engine.py`).
   - Produce inventory and weight compatibility (`produce.py`, `produce_engine.py`).
5. **Branch:** `feature/phase2-lakshya-orders-batches` (Lakshya Raj Malviya — Commits 01, 02, 03)
   - Canonical 5-state order lifecycle (`order_engine.py`).
   - Dual-capacity dynamic batch engine (`batch_engine.py`).
   - Atomic order checkout & batch allocation (`routers/orders.py`).
6. **Branch:** `feature/phase2-hemant-logistics-payments` (Hemant Yadav — Commits 01, 02, 03)
   - Logistics zones, drop points, and fleet dispatch (`routers/logistics.py`, `logistics_engine.py`).
   - Receiver delivery confirmation without OTP (`routers/logistics.py`).
   - Pluggable Mock & Razorpay payment gateways and paise ledger (`routers/payments.py`, `payment_gateways/*`).

---

### Wave 4: Dispute Subsystem & Presentation Tier
*PR Merge Order:*
7. **Branch:** `feature/phase2-aparna-testing` (Aparna Jha — Commit 02)
   - 24-hour dispute subsystem with photo evidence uploads (`routers/disputes.py`, `dispute_engine.py`).
8. **Branch:** `feature/phase2-raksha-frontend` (Raksha Pandey — Commits 01, 02)
   - Shared API client (`api.js`, `auth.js`) and CSS design system (`style.css`).
9. **Branch:** `feature/phase2-harshika-dashboards` (Harshika Singh — Commits 01, 02, 03)
   - Buyer and Farmer interactive workflows (`dashboard.html`, `dashboard.js`).
   - Logistics and Admin management controls.
   - Dispute photo upload modals, escrow counters, and Hindi localization (`lang.js`).

---

### Wave 5: Deployment Runtime & Specialized Research
*PR Merge Order:*
10. **Branch:** `feature/phase2-anshika-deployment` (Anshika Sharma — Commit 02)
    - FastAPI lifespan startup hooks, upload directory creation, Dockerfile, and operations runbook.
11. **Branch:** `feature/phase2-mansi-metrics` (Mansi Jain — Commit 01)
    - Operational metrics report (`phase-2-operational-metrics-review.md`) and data quality review.
12. **Branch:** `feature/phase2-alankrit-ml-review` (Alankrit Purohit — Commit 01)
    - AI/ML feasibility assessment and batch optimization analysis (`ml-feasibility-report.md`).

---

### Wave 6: Final End-to-End Test Suite & Release Certification
*PR Merge Order:*
13. **Branch:** `feature/phase2-aparna-testing` (Aparna Jha — Commits 01, 03)
    - Comprehensive test suites (`test_batches_phase2.py`, `test_disputes_phase2.py`, `test_payment_gateway_phase2.py`, `test_phase2_workflows.py`).
    - Validates 50/50 automated tests passing.
14. **Branch:** `feature/phase2-sneha-qa` (Sneha Sanodia — Commit 02)
    - Phase 2 completion report, test report, root README update, and release certification.
