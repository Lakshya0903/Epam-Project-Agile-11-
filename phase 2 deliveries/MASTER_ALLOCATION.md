# FarmCart Phase 2 — Master Work Allocation Document

**Project:** FarmCart Phase 2 Master Implementation  
**Team:** Agile 11  
**Generated:** November 2026  

---

## 1. Executive Summary Table

| Member | Role | Commit Count | Assigned Task Directories | Primary Modules |
|---|---|:---:|---|---|
| **Sneha Sanodiya** | Team Lead + QA Lead | 2 | `Commit_01_Baseline_And_Gap_Analysis`<br/>`Commit_02_Integration_Review_And_Release_Readiness` | `phase-2-baseline-audit.md`, `phase-2-architecture.md`, `phase-2-security-review.md`, `README.md`... |
| **Lakshya Raj Malviya** | Backend Lead + AI/ML Engineer | 3 | `Commit_01_Order_Engine_And_Lifecycle`<br/>`Commit_02_Automatic_Batch_Engine`<br/>`Commit_03_Order_Batch_Logistics_Integration` | `order_engine.py`, `batch_engine.py`, `orders.py`... |
| **Yash Goyal** | Backend Developer | 2 | `Commit_01_Nationwide_Serviceability_Engine`<br/>`Commit_02_Produce_Inventory_Compatibility` | `serviceability_engine.py`, `geo.py`, `produce.py`, `produce_engine.py`... |
| **Hemant Yadav** | Backend Developer 3 | 3 | `Commit_01_Logistics_API_And_Fleet_Management`<br/>`Commit_02_Receiver_Confirmation_Without_OTP`<br/>`Commit_03_Payment_API_And_Gateway_Integration` | `logistics.py`, `logistics_engine.py`, `logistics.py`, `otp.py`... |
| **Swyam Shukla** | Database Lead + API Integration Engineer 1 | 3 | `Commit_01_Database_Models_And_Relationships`<br/>`Commit_02_Pydantic_Schemas_And_Data_Contracts`<br/>`Commit_03_Alembic_Migrations_And_Database_Seeding` | `models.py`, `schemas.py`, `phase-2-api-contracts.md`, `alembic.ini`... |
| **Raksha Pandey** | Frontend Lead + Database Developer 1 | 2 | `Commit_01_Shared_API_Client_And_Auth`<br/>`Commit_02_Shared_Design_System_And_Layout` | `api.js`, `auth.js`, `index.html`, `style.css`... |
| **Harshika Singh** | Research Lead + Frontend Developer 2 | 3 | `Commit_01_Buyer_And_Farmer_Dashboards`<br/>`Commit_02_Logistics_And_Admin_Dashboards`<br/>`Commit_03_Dispute_Payment_Interface_And_Localization` | `dashboard.html`, `dashboard.js`, `dashboard.html`, `dashboard.js`... |
| **Anshika Sharma** | Backend Developer 1 + Deployment Manager | 2 | `Commit_01_Environment_And_Dependency_Configuration`<br/>`Commit_02_Application_Startup_And_Docker_Integration` | `config.py`, `.env.example`, `requirements.txt`, `.gitignore`... |
| **Aparna Jha** | Testing Engineer + Research Engineer | 3 | `Commit_01_Serviceability_And_Batch_Testing`<br/>`Commit_02_Order_Delivery_And_Dispute_Testing`<br/>`Commit_03_Payment_Gateway_And_End_To_End_Testing` | `test_serviceability_phase2.py`, `test_batches_phase2.py`, `test_logistics.py`, `test_orders.py`... |
| **Mansi Jain** | Data Analyst + Testing Engineer | 1 | `Commit_01_Phase2_Data_Quality_And_Metrics_Review` | `phase-2-operational-metrics-review.md`, `data_quality.py`, `mandi_analysis.py`... |
| **Alankrit Purohit** | AI/ML Lead | 1 | `Commit_01_AI_ML_Feasibility_And_Optimization_Assessment` | `ml-feasibility-report.md`, `README.md`, `evaluation.py`, `price_predictor.py`... |

---

## 2. Detailed Member-by-Member Breakdown

### Sneha Sanodiya (`snehasanodia1@gmail.com`) — Team Lead + QA Lead
- **Deliverables Path:** `Sneha_Sanodia/Deliverables/Phase2_QA_Coordination/`
- **Assigned Git Branch:** `feature/phase2-sneha-qa`
- **Total Commits:** 2

#### Commit 01: `Commit_01_Baseline_And_Gap_Analysis`
- **Title:** Phase 2 Baseline Audit and Architecture Specification
- **Objective:** Audit the Phase 1 codebase, formalize the Phase 2 architectural baseline, map cross-module dependencies, and document feature gap analysis.
- **Assigned Files:**
  - `docs/phase-2-baseline-audit.md`
  - `docs/phase-2-architecture.md`
  - `docs/phase-2-security-review.md`
- **Dependencies:** None. This is the foundational kickoff and architecture baseline for Phase 2.
- **Proposed Commit Header:** `docs(audit): formalize Phase 2 architecture baseline, security review and gap analysis`

#### Commit 02: `Commit_02_Integration_Review_And_Release_Readiness`
- **Title:** Phase 2 Integration Verification and Final Release Readiness
- **Objective:** Perform end-to-end integration tracking, coordinate QA acceptance criteria, verify automated test pass status (50/50 tests), and prepare release documentation.
- **Assigned Files:**
  - `README.md`
  - `docs/phase-2-completion-report.md`
  - `docs/phase-2-test-report.md`
- **Dependencies:** Depends on Aparna Jha's test results, Lakshya/Hemant/Yash's backend services, and Harshika/Raksha's frontend UI.
- **Proposed Commit Header:** `docs(release): compile Phase 2 completion report, test verification, and project README`

### Lakshya Raj Malviya (`177052558+Lakshya0903@users.noreply.github.com`) — Backend Lead + AI/ML Engineer
- **Deliverables Path:** `Lakshya_Raj_Malviya/Deliverables/Phase2_Backend_Engineering/`
- **Assigned Git Branch:** `feature/phase2-lakshya-orders-batches`
- **Total Commits:** 3

#### Commit 01: `Commit_01_Order_Engine_And_Lifecycle`
- **Title:** Canonical 5-State Order Lifecycle and Reservation Engine
- **Objective:** Implement the canonical 5-state order lifecycle (PLACED -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED), status history tracking, and inventory reservation rollback.
- **Assigned Files:**
  - `backend/app/services/order_engine.py`
- **Dependencies:** Depends on Swyam Shukla's OrderStatus and OrderStatusHistory models.
- **Proposed Commit Header:** `feat(order): implement canonical 5-state lifecycle and inventory reservation`

#### Commit 02: `Commit_02_Automatic_Batch_Engine`
- **Title:** Dual-Capacity Delivery Batch Engine and Schedule Cutoffs
- **Objective:** Build the dynamic dual-capacity delivery batch engine that enforces both maximum weight (kg) and maximum order count limits, calculates scheduling cutoffs, and isolates drop points.
- **Assigned Files:**
  - `backend/app/services/batch_engine.py`
- **Dependencies:** Depends on Swyam Shukla's DeliveryBatch model and Yash Goyal's zone serviceability logic.
- **Proposed Commit Header:** `feat(batch): implement dual-capacity delivery batch engine and cutoff scheduling`

#### Commit 03: `Commit_03_Order_Batch_Logistics_Integration`
- **Title:** Transactional Order Checkout and Automatic Batch Assignment
- **Objective:** Integrate the order router with the dual-capacity batch engine and serviceability validator to guarantee atomic order creation, inventory reservation, and batch allocation.
- **Assigned Files:**
  - `backend/app/routers/orders.py`
- **Dependencies:** Depends on Commit 01 & 02, Yash Goyal's serviceability_engine, and Swyam Shukla's schemas.
- **Proposed Commit Header:** `feat(orders): integrate order checkout with batch allocation and serviceability`

### Yash Goyal (`yashgoyal09102005@gmail.com`) — Backend Developer
- **Deliverables Path:** `Yash_Goyal/Deliverables/Phase2_Backend_Modules/`
- **Assigned Git Branch:** `feature/phase2-yash-serviceability`
- **Total Commits:** 2

#### Commit 01: `Commit_01_Nationwide_Serviceability_Engine`
- **Title:** Nationwide Indian PIN Code Serviceability Engine
- **Objective:** Implement nationwide Indian PIN code validation, delivery zone mapping, and delivery mode eligibility evaluation (home delivery vs shared drop points).
- **Assigned Files:**
  - `backend/app/services/serviceability_engine.py`
  - `backend/app/utils/geo.py`
- **Dependencies:** Depends on Swyam Shukla's DeliveryZone and SharedDropPoint ORM models.
- **Proposed Commit Header:** `feat(serviceability): implement Indian PIN validator and zone serviceability engine`

#### Commit 02: `Commit_02_Produce_Inventory_Compatibility`
- **Title:** Produce Inventory Management and Weight Compatibility
- **Objective:** Update produce endpoints and produce engine to enforce quantity availability, weight consistency for batching, and preserve Phase 1 farmer listing capabilities.
- **Assigned Files:**
  - `backend/app/routers/produce.py`
  - `backend/app/services/produce_engine.py`
- **Dependencies:** Depends on Swyam Shukla's Produce and User models.
- **Proposed Commit Header:** `feat(produce): enhance produce inventory validation and batch weight compatibility`

### Hemant Yadav (`hemantyadav6090@gmail.com`) — Backend Developer 3
- **Deliverables Path:** `Hemant_Yadav/Deliverables/Phase2_Logistics_And_Payments/`
- **Assigned Git Branch:** `feature/phase2-hemant-logistics-payments`
- **Total Commits:** 3

#### Commit 01: `Commit_01_Logistics_API_And_Fleet_Management`
- **Title:** Logistics Zone, Drop Point and Fleet APIs
- **Objective:** Implement REST endpoints for delivery zones, drop points, vehicle fleet allocation, and delivery batch tracking.
- **Assigned Files:**
  - `backend/app/routers/logistics.py`
  - `backend/app/services/logistics_engine.py`
- **Dependencies:** Depends on Swyam Shukla's schemas/models and Yash Goyal's geo utilities.
- **Proposed Commit Header:** `feat(logistics): add delivery zones, drop points, and batch dispatch APIs`

#### Commit 02: `Commit_02_Receiver_Confirmation_Without_OTP`
- **Title:** Receiver Delivery Confirmation Without OTP
- **Objective:** Implement the authenticated receiver delivery confirmation endpoint, transitioning orders to DELIVERED without SMS OTP friction.
- **Assigned Files:**
  - `backend/app/routers/logistics.py`
  - `backend/app/utils/otp.py`
- **Dependencies:** Depends on Lakshya's order state transitions and Swyam's Delivery model.
- **Proposed Commit Header:** `feat(logistics): implement receiver delivery confirmation without OTP`

#### Commit 03: `Commit_03_Payment_API_And_Gateway_Integration`
- **Title:** Pluggable Payment Gateway Integration and Integer Paise Ledger
- **Objective:** Implement payment initiation, verification, webhook endpoints, pluggable Mock and Razorpay providers, and an immutable integer paise escrow ledger.
- **Assigned Files:**
  - `backend/app/routers/payments.py`
  - `backend/app/services/payment_engine.py`
  - `backend/app/services/payment_gateways/__init__.py`
  - `backend/app/services/payment_gateways/base.py`
  - `backend/app/services/payment_gateways/mock_provider.py`
  - `backend/app/services/payment_gateways/razorpay_provider.py`
  - `docs/phase-2-payment-gateway.md`
- **Dependencies:** Depends on Swyam Shukla's payment models/schemas and Anshika's config settings.
- **Proposed Commit Header:** `feat(payments): implement pluggable payment gateways and integer paise ledger`

### Swyam Shukla (`swyamshukla0104@gmail.com`) — Database Lead + API Integration Engineer 1
- **Deliverables Path:** `Swyam_Shukla/Deliverables/Phase2_Database_And_API_Schemas/`
- **Assigned Git Branch:** `feature/phase2-swyam-database`
- **Total Commits:** 3

#### Commit 01: `Commit_01_Database_Models_And_Relationships`
- **Title:** SQLAlchemy ORM Models and Phase 2 Relational Schema
- **Objective:** Define and extend SQLAlchemy Declarative models supporting delivery zones, drop points, delivery batches, canonical order status history, disputes, evidence, and financial ledger.
- **Assigned Files:**
  - `backend/app/models.py`
- **Dependencies:** None. Foundational data schema definition for all backend services.
- **Proposed Commit Header:** `feat(database): extend SQLAlchemy models for Phase 2 logistics, disputes, and escrow`

#### Commit 02: `Commit_02_Pydantic_Schemas_And_Data_Contracts`
- **Title:** Pydantic Schemas and API Contract Specifications
- **Objective:** Define strict Pydantic v2 validation schemas for request bodies, responses, PIN normalization, dispute filings, batch assignments, and gateway payloads.
- **Assigned Files:**
  - `backend/app/schemas.py`
  - `docs/phase-2-api-contracts.md`
- **Dependencies:** Depends on Commit 01 models.
- **Proposed Commit Header:** `feat(schemas): create Pydantic validation schemas and Phase 2 API data contracts`

#### Commit 03: `Commit_03_Alembic_Migrations_And_Database_Seeding`
- **Title:** Alembic Database Migrations and Seed Data Management
- **Objective:** Configure Alembic batch mode migrations for SQLite/PostgreSQL compatibility, generate revision 22f82a866cc9, update seed data fixtures, and document migration runbooks.
- **Assigned Files:**
  - `backend/alembic.ini`
  - `backend/alembic/README`
  - `backend/alembic/env.py`
  - `backend/alembic/script.py.mako`
  - `backend/alembic/versions/22f82a866cc9_phase_2_delivery_batches_disputes_.py`
  - `backend/seed.py`
  - `Documents/database-migrations.md`
  - `docs/phase-2-database-changes.md`
- **Dependencies:** Depends on Commit 01 & 02.
- **Proposed Commit Header:** `feat(migration): configure Alembic batch migrations and Phase 2 seed data`

### Raksha Pandey (`raksha.pandeyyy@gmail.com`) — Frontend Lead + Database Developer 1
- **Deliverables Path:** `Raksha_Pandey/Deliverables/Phase2_Shared_Frontend/`
- **Assigned Git Branch:** `feature/phase2-raksha-frontend`
- **Total Commits:** 2

#### Commit 01: `Commit_01_Shared_API_Client_And_Auth`
- **Title:** Shared API Client and Authentication Session Wrapper
- **Objective:** Build the shared frontend API communication layer, JWT bearer token handling, session management, multipart/form-data upload helpers, and standardized error banners.
- **Assigned Files:**
  - `frontend/js/api.js`
  - `frontend/js/auth.js`
  - `frontend/index.html`
- **Dependencies:** Depends on Swyam Shukla's API contracts and backend auth endpoints.
- **Proposed Commit Header:** `feat(frontend): build shared API client wrapper and JWT session manager`

#### Commit 02: `Commit_02_Shared_Design_System_And_Layout`
- **Title:** Shared Responsive CSS Design System and UI Component Styles
- **Objective:** Implement the shared CSS3 design system, responsive grid layouts, card styles, status badges for all 5 canonical order states, dispute flags, and modal dialogs.
- **Assigned Files:**
  - `frontend/css/style.css`
- **Dependencies:** Depends on Commit 01.
- **Proposed Commit Header:** `style(ui): implement responsive CSS design system and Phase 2 status badges`

### Harshika Singh (`harshikasingh212@gmail.com`) — Research Lead + Frontend Developer 2
- **Deliverables Path:** `Harshika_Singh/Deliverables/Phase2_Dashboard_Development/`
- **Assigned Git Branch:** `feature/phase2-harshika-dashboards`
- **Total Commits:** 3

#### Commit 01: `Commit_01_Buyer_And_Farmer_Dashboards`
- **Title:** Buyer and Farmer Dashboard User Workflows
- **Objective:** Implement interactive Buyer and Farmer workflows in dashboard.html and dashboard.js, connecting produce browsing, address checkout, order tracking, and farmer order fulfillment.
- **Assigned Files:**
  - `frontend/dashboard.html`
  - `frontend/js/dashboard.js`
- **Dependencies:** Depends on Raksha Pandey's api.js and backend order/produce endpoints.
- **Proposed Commit Header:** `feat(dashboard): implement Buyer and Farmer interactive workflows`

#### Commit 02: `Commit_02_Logistics_And_Admin_Dashboards`
- **Title:** Logistics Partner and Platform Admin Dashboards
- **Objective:** Build the Logistics Partner fleet dispatch interface and the Platform Admin management dashboard for delivery zones, drop points, and batch monitoring.
- **Assigned Files:**
  - `frontend/dashboard.html`
  - `frontend/js/dashboard.js`
- **Dependencies:** Depends on Commit 01 and Hemant Yadav's logistics APIs.
- **Proposed Commit Header:** `feat(dashboard): build Logistics fleet management and Admin zone controls`

#### Commit 03: `Commit_03_Dispute_Payment_Interface_And_Localization`
- **Title:** Dispute Filing Interface, Payment Status and Multi-lingual Localization
- **Objective:** Implement the buyer dispute filing modal with photo evidence upload, admin reviewer dispute adjudication screens, payment escrow status indicators, and Hindi/English localization.
- **Assigned Files:**
  - `frontend/dashboard.html`
  - `frontend/js/dashboard.js`
  - `frontend/js/lang.js`
  - `frontend/analytics.html`
  - `frontend/js/analytics.js`
- **Dependencies:** Depends on Commit 01 & 02, Aparna's dispute engine, and Hemant's payment endpoints.
- **Proposed Commit Header:** `feat(ui): add dispute photo upload modal, escrow UI, and Hindi localization`

### Anshika Sharma (`anshika2907sharma@gmail.com`) — Backend Developer 1 + Deployment Manager
- **Deliverables Path:** `Anshika_Sharma/Deliverables/Phase2_Deployment_Integration/`
- **Assigned Git Branch:** `feature/phase2-anshika-deployment`
- **Total Commits:** 2

#### Commit 01: `Commit_01_Environment_And_Dependency_Configuration`
- **Title:** Application Configuration, Environment Variables and Dependencies
- **Objective:** Define Phase 2 environment variables (Razorpay gateway credentials, upload directories, batch defaults, dispute windows), update requirements.txt, and configure .env.example.
- **Assigned Files:**
  - `backend/app/config.py`
  - `backend/.env.example`
  - `backend/requirements.txt`
  - `backend/.gitignore`
- **Dependencies:** None. Configuration baseline for all backend components.
- **Proposed Commit Header:** `chore(config): formalize Phase 2 settings, environment variables, and dependencies`

#### Commit 02: `Commit_02_Application_Startup_And_Docker_Integration`
- **Title:** FastAPI Application Factory, Lifespan Hooks and Docker Setup
- **Objective:** Configure the FastAPI application lifespan, mount routers, configure CORS, initialize upload directories, update the Dockerfile, and document operations.
- **Assigned Files:**
  - `backend/Dockerfile`
  - `backend/app/main.py`
  - `docs/phase-2-operations-runbook.md`
- **Dependencies:** Depends on Commit 01 and all API routers.
- **Proposed Commit Header:** `feat(deployment): configure FastAPI lifespan, upload directory mounts, and Dockerfile`

### Aparna Jha (`aparnajha2021@gmail.com`) — Testing Engineer + Research Engineer
- **Deliverables Path:** `Aparna_Jha/Deliverables/Phase2_Test_Engineering/`
- **Assigned Git Branch:** `feature/phase2-aparna-testing`
- **Total Commits:** 3

#### Commit 01: `Commit_01_Serviceability_And_Batch_Testing`
- **Title:** Serviceability, Zone Lookup and Dual-Capacity Batch Test Suites
- **Objective:** Implement comprehensive automated test suites for Indian PIN code validation, zone serviceability, dual-capacity batching thresholds, and schedule cutoff enforcement.
- **Assigned Files:**
  - `tests/test_serviceability_phase2.py`
  - `tests/test_batches_phase2.py`
  - `tests/test_logistics.py`
- **Dependencies:** Depends on Lakshya's batch_engine and Yash's serviceability_engine.
- **Proposed Commit Header:** `test(batches): add unit and integration test suites for zones and dual-capacity batches`

#### Commit 02: `Commit_02_Order_Delivery_And_Dispute_Testing`
- **Title:** Order Lifecycle, Receiver Confirmation and Dispute Subsystem
- **Objective:** Build automated tests for canonical order state transitions, receiver confirmation without OTP, 24-hour dispute window enforcement, evidence photo upload, and reviewer resolution.
- **Assigned Files:**
  - `tests/test_orders.py`
  - `tests/test_delivery_confirmation_phase2.py`
  - `tests/test_disputes_phase2.py`
  - `backend/app/routers/disputes.py`
  - `backend/app/services/dispute_engine.py`
- **Dependencies:** Depends on Lakshya's order engine and Hemant's receiver confirmation.
- **Proposed Commit Header:** `feat(disputes): implement dispute engine, router, and comprehensive test suite`

#### Commit 03: `Commit_03_Payment_Gateway_And_End_To_End_Testing`
- **Title:** Payment Gateway Test Suite and End-to-End Workflow Verification
- **Objective:** Implement automated tests for Mock and Razorpay payment gateways, webhook signature verification, integer paise accounting, and complete buyer-to-delivery workflows.
- **Assigned Files:**
  - `tests/test_payment_gateway_phase2.py`
  - `tests/test_payments.py`
  - `tests/test_phase2_workflows.py`
  - `tests/test_auth.py`
  - `tests/test_produce.py`
- **Dependencies:** Depends on Commit 01 & 02 and all Phase 2 backend/frontend modules.
- **Proposed Commit Header:** `test(e2e): add payment gateway tests and complete end-to-end workflow validation`

### Mansi Jain (`mansijain1618@gmail.com`) — Data Analyst + Testing Engineer
- **Deliverables Path:** `Mansi_Jain/Deliverables/Phase2_Data_Quality_Review/`
- **Assigned Git Branch:** `feature/phase2-mansi-metrics`
- **Total Commits:** 1

#### Commit 01: `Commit_01_Phase2_Data_Quality_And_Metrics_Review`
- **Title:** Phase 2 Operational Reporting, Data Quality and KPI Formulations
- **Objective:** Analyze Phase 2 operational data models, formulate Key Performance Indicators (batch fill rate, cutoff misses, delivery delay, dispute latency, escrow hold time), and document data quality checks.
- **Assigned Files:**
  - `docs/phase-2-operational-metrics-review.md`
  - `analytics/data_quality.py`
  - `analytics/mandi_analysis.py`
- **Dependencies:** Depends on Swyam Shukla's data models and database changes.
- **Proposed Commit Header:** `docs(analytics): establish Phase 2 operational metrics and data quality framework`

### Alankrit Purohit (`purohitak21@gmail.com`) — AI/ML Lead
- **Deliverables Path:** `Alankrit_Purohit/Deliverables/Phase2_ML_Feasibility/`
- **Assigned Git Branch:** `feature/phase2-alankrit-ml-review`
- **Total Commits:** 1

#### Commit 01: `Commit_01_AI_ML_Feasibility_And_Optimization_Assessment`
- **Title:** Phase 2 AI/ML Feasibility Assessment and Optimization Study
- **Objective:** Evaluate whether machine learning is necessary or beneficial for Phase 2 delivery batching and route optimization, review the deterministic business rule engine, and document justified architectural recommendations.
- **Assigned Files:**
  - `docs/ml-feasibility-report.md`
  - `ml/README.md`
  - `ml/evaluation.py`
  - `ml/price_predictor.py`
  - `ml/experiments/baseline_experiment.py`
  - `ml/experiments/dataset_generator.py`
- **Dependencies:** Depends on Lakshya's batch_engine and Hemant's logistics_engine.
- **Proposed Commit Header:** `docs(ml): assess AI/ML feasibility for batch optimization and validate deterministic baseline`
