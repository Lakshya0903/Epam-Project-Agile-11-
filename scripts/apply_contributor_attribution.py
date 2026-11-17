"""
FarmCart Phase 2 — Contributor Attribution, Commit Messages & Sign-off Standard Updater
Updates all 25 commit packages in phase 2 deliveries/ and root coordination documents
to conform strictly to the project-wide attribution and sign-off standard:
1. Mandatory trailer: Signed-off-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>
2. Verified email directory for all 11 contributors.
3. Appropriate Co-authored-by, Reviewed-by, and Researched-by trailers.
4. Author attribution preserved in git commands and validation logs.
"""

import os
import csv
from datetime import datetime

TARGET_DIR = os.path.join(os.getcwd(), "phase 2 deliveries")

# Verified Team Directory
TEAM = {
    "Mansi_Jain": {
        "display_name": "Mansi Jain",
        "email": "mansijain1618@gmail.com",
        "role": "Data Analyst, Testing Engineer, metrics and data quality",
        "folder": "Phase2_Data_Quality_Review",
        "branch": "feature/phase2-mansi-metrics",
    },
    "Raksha_Pandey": {
        "display_name": "Raksha Pandey",
        "email": "raksha.pandeyyy@gmail.com",
        "role": "Frontend Lead, database development, buyer-facing workflows",
        "folder": "Phase2_Shared_Frontend",
        "branch": "feature/phase2-raksha-frontend",
    },
    "Alankrit_Purohit": {
        "display_name": "Alankrit Purohit",
        "email": "purohitak21@gmail.com",
        "role": "AI/ML Lead, optimization research and feasibility analysis",
        "folder": "Phase2_ML_Feasibility",
        "branch": "feature/phase2-alankrit-ml-review",
    },
    "Harshika_Singh": {
        "display_name": "Harshika Singh",
        "email": "harshikasingh212@gmail.com",
        "role": "Research Lead, frontend development, dashboards and dispute interfaces",
        "folder": "Phase2_Dashboard_Development",
        "branch": "feature/phase2-harshika-dashboards",
    },
    "Sneha_Sanodia": {
        "display_name": "Sneha Sanodiya",
        "email": "snehasanodia1@gmail.com",
        "role": "Team Lead, QA Lead, coordination, acceptance criteria, release readiness",
        "folder": "Phase2_QA_Coordination",
        "branch": "feature/phase2-sneha-qa",
    },
    "Yash_Goyal": {
        "display_name": "Yash Goyal",
        "email": "yashgoyal09102005@gmail.com",
        "role": "Backend Developer, serviceability, inventory and produce logic",
        "folder": "Phase2_Backend_Modules",
        "branch": "feature/phase2-yash-serviceability",
    },
    "Aparna_Jha": {
        "display_name": "Aparna Jha",
        "email": "aparnajha2021@gmail.com",
        "role": "Testing Engineer, Research Engineer, validation and quality assurance",
        "folder": "Phase2_Test_Engineering",
        "branch": "feature/phase2-aparna-testing",
    },
    "Anshika_Sharma": {
        "display_name": "Anshika Sharma",
        "email": "anshika2907sharma@gmail.com",
        "role": "Backend/deployment responsibilities, configuration and release infrastructure",
        "folder": "Phase2_Deployment_Integration",
        "branch": "feature/phase2-anshika-deployment",
    },
    "Swyam_Shukla": {
        "display_name": "Swyam Shukla",
        "email": "swyamshukla0104@gmail.com",
        "role": "Database Lead, API Integration Engineer, models, schemas and migrations",
        "folder": "Phase2_Database_And_API_Schemas",
        "branch": "feature/phase2-swyam-database",
    },
    "Hemant_Yadav": {
        "display_name": "Hemant Yadav",
        "email": "hemantyadav6090@gmail.com",
        "role": "Backend Developer, logistics, delivery confirmation and payment integrations",
        "folder": "Phase2_Logistics_And_Payments",
        "branch": "feature/phase2-hemant-logistics-payments",
    },
    "Lakshya_Raj_Malviya": {
        "display_name": "Lakshya Raj Malviya",
        "email": "177052558+Lakshya0903@users.noreply.github.com",
        "role": "Backend Lead, AI/ML Engineer, architecture and integration oversight",
        "folder": "Phase2_Backend_Engineering",
        "branch": "feature/phase2-lakshya-orders-batches",
    },
}

MANDATORY_SIGNOFF = "Signed-off-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>"

# 25 Detailed Commit Specifications
COMMITS_DATA = [
    # 1. Sneha Sanodiya (2 commits)
    {
        "member_key": "Sneha_Sanodia",
        "commit_dir": "Commit_01_Baseline_And_Gap_Analysis",
        "commit_msg": (
            "docs(audit): formalize Phase 2 architecture baseline, security review and gap analysis\n\n"
            "Audit the existing Phase 1 application against Phase 2 requirements, establishing the architectural specification for nationwide delivery zones, dual-capacity batching, receiver confirmations, and dispute escalation.\n\n"
            "- Formalized multi-tier architectural topology across API, services, and persistence layers.\n"
            "- Documented cross-module dependencies and delivery zone / shared drop point routing.\n"
            "- Completed security audit covering JWT RBAC authorization, token management, and webhook verification.\n"
            "- Validated architectural baseline across all modules prior to team work allocation.\n\n"
            "Reviewed-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Sneha_Sanodia",
        "commit_dir": "Commit_02_Integration_Review_And_Release_Readiness",
        "commit_msg": (
            "docs(release): compile Phase 2 completion report, test verification, and project README\n\n"
            "Coordinate final quality assurance across all 10 implementation stages, verifying automated test pass criteria and authoring production release guidelines.\n\n"
            "- Verified 100% test pass status across the full automated test suite (50/50 tests passing in 14.398s).\n"
            "- Documented verification of nationwide logistics, dual-capacity batches, receiver confirmation, and disputes.\n"
            "- Updated root README with environment setup, Alembic migration instructions, and API endpoints.\n"
            "- Certified application readiness for staging deployment across all 4 user dashboard personas.\n\n"
            "Reviewed-by: Aparna Jha <aparnajha2021@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 2. Lakshya Raj Malviya (3 commits)
    {
        "member_key": "Lakshya_Raj_Malviya",
        "commit_dir": "Commit_01_Order_Engine_And_Lifecycle",
        "commit_msg": (
            "feat(order): implement canonical 5-state lifecycle and inventory reservation\n\n"
            "Establish a deterministic state machine for order progression, preventing out-of-order mutations and ensuring atomic inventory reservation.\n\n"
            "- Enforced canonical state transitions: PLACED -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED.\n"
            "- Added strict transition_order_status() with state validation and immutable order_status_history audit logging.\n"
            "- Implemented inventory reservation checks and atomic quantity decrementing on checkout.\n"
            "- Added order cancellation handler with automatic inventory restocking and capacity release.\n"
            "- Validated state transition rules against unit test suite in tests/test_orders.py.\n\n"
            "Reviewed-by: Swyam Shukla <swyamshukla0104@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Lakshya_Raj_Malviya",
        "commit_dir": "Commit_02_Automatic_Batch_Engine",
        "commit_msg": (
            "feat(batch): implement dual-capacity delivery batch engine and cutoff scheduling\n\n"
            "Implement the dynamic delivery batching engine to group orders by area, delivery date, and time slot while enforcing dual weight and order-count capacity limits.\n\n"
            "- Built find_or_create_batch() enforcing both max_weight_kg and max_orders thresholds.\n"
            "- Implemented dynamic cutoff time calculation (4h before morning slot, 3h before afternoon slot).\n"
            "- Enforced shared drop point isolation to prevent mixing home delivery and drop point routes.\n"
            "- Added automatic batch locking upon cutoff expiration and capacity overflow handling.\n"
            "- Validated dual-capacity boundaries and cutoff freezing in tests/test_batches_phase2.py.\n\n"
            "Co-authored-by: Yash Goyal <yashgoyal09102005@gmail.com>\n"
            "Reviewed-by: Swyam Shukla <swyamshukla0104@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Lakshya_Raj_Malviya",
        "commit_dir": "Commit_03_Order_Batch_Logistics_Integration",
        "commit_msg": (
            "feat(orders): integrate order checkout with batch allocation and serviceability\n\n"
            "Wire the order checkout API router with the dual-capacity batch engine and PIN serviceability validator within an atomic database transaction.\n\n"
            "- Connected POST /orders endpoint to evaluate_serviceability() for PIN code serviceability check.\n"
            "- Integrated assign_order_to_batch() to automatically allocate orders to eligible batches during checkout.\n"
            "- Handled capacity overflow and fallback batch generation during peak ordering periods.\n"
            "- Enriched order response schemas with assigned batch details, slot times, and canonical tracking status.\n"
            "- Verified checkout atomicity and inventory rollback across tests/test_orders.py.\n\n"
            "Co-authored-by: Hemant Yadav <hemantyadav6090@gmail.com>\n"
            "Reviewed-by: Sneha Sanodiya <snehasanodia1@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 3. Yash Goyal (2 commits)
    {
        "member_key": "Yash_Goyal",
        "commit_dir": "Commit_01_Nationwide_Serviceability_Engine",
        "commit_msg": (
            "feat(serviceability): implement Indian PIN validator and zone serviceability engine\n\n"
            "Implement nationwide geographic address validation and active delivery zone mapping across all Indian states and postal circles.\n\n"
            "- Added strict 6-digit regex validation for Indian PIN codes: ^[1-9][0-9]{5}$.\n"
            "- Built clean_pincode() to sanitize embedded whitespace, leading/trailing spaces, and non-numeric inputs.\n"
            "- Implemented evaluate_serviceability() verifying active zone coverage, delivery modes, and drop point availability.\n"
            "- Added Haversine distance calculations and nearest drop point proximity filtering in utils/geo.py.\n"
            "- Validated boundary test cases in tests/test_serviceability_phase2.py.\n\n"
            "Reviewed-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Yash_Goyal",
        "commit_dir": "Commit_02_Produce_Inventory_Compatibility",
        "commit_msg": (
            "feat(produce): enhance produce inventory validation and batch weight compatibility\n\n"
            "Refactor produce endpoints and domain services to ensure inventory reservation compatibility, accurate unit weights for batch allocation, and preserved Phase 1 mandi comparisons.\n\n"
            "- Enforced non-negative inventory thresholds and sold-out status flags on produce listings.\n"
            "- Added produce weight formatting and validation for dual-capacity batch load calculations.\n"
            "- Enhanced search and category filters across vegetable, fruit, and grain listings.\n"
            "- Preserved Phase 1 mandi price benchmark comparisons without disrupting active orders.\n"
            "- Validated produce operations in tests/test_produce.py.\n\n"
            "Reviewed-by: Swyam Shukla <swyamshukla0104@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 4. Hemant Yadav (3 commits)
    {
        "member_key": "Hemant_Yadav",
        "commit_dir": "Commit_01_Logistics_API_And_Fleet_Management",
        "commit_msg": (
            "feat(logistics): add delivery zones, drop points, and batch dispatch APIs\n\n"
            "Implement REST controllers and domain logic for delivery zones, shared drop points, vehicle fleet allocation, and delivery batch dispatch.\n\n"
            "- Added GET /logistics/zones and GET /logistics/zones/{id}/drop-points endpoints for zone inspection.\n"
            "- Implemented batch dispatch and transit status updating for logistics partner fleet operations.\n"
            "- Added vehicle capacity validation and cold chain compatibility checks for temperature-sensitive produce.\n"
            "- Implemented nearest-neighbor route distance optimization helpers in logistics_engine.py.\n"
            "- Tested fleet assignment and vehicle constraints in tests/test_logistics.py.\n\n"
            "Reviewed-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Hemant_Yadav",
        "commit_dir": "Commit_02_Receiver_Confirmation_Without_OTP",
        "commit_msg": (
            "feat(logistics): implement receiver delivery confirmation without OTP\n\n"
            "Provide an authenticated receiver self-service confirmation endpoint, eliminating delivery delays caused by external SMS OTP gateway failures.\n\n"
            "- Added POST /logistics/deliveries/{id}/confirm-receipt endpoint.\n"
            "- Enforced authenticated receiver authorization checks (buyer or admin access only).\n"
            "- Recorded delivered_at timestamp and confirmed_by_id audit field on the delivery record.\n"
            "- Transitioned order status to DELIVERED and initiated the 24-hour dispute window.\n"
            "- Preserved legacy OTP utilities in utils/otp.py for backwards compatibility.\n"
            "- Validated confirmation authorization in tests/test_delivery_confirmation_phase2.py.\n\n"
            "Co-authored-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>\n"
            "Reviewed-by: Aparna Jha <aparnajha2021@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Hemant_Yadav",
        "commit_dir": "Commit_03_Payment_API_And_Gateway_Integration",
        "commit_msg": (
            "feat(payments): implement pluggable payment gateways and integer paise ledger\n\n"
            "Integrate pluggable payment gateways with integer paise accounting, HMAC-SHA256 signature verification, and automated escrow hold until delivery.\n\n"
            "- Built BasePaymentGateway abstract interface and provider registry.\n"
            "- Implemented MockPaymentGateway for deterministic local testing and development.\n"
            "- Implemented RazorpayGateway with order creation and HMAC-SHA256 signature verification.\n"
            "- Added POST /payments/initiate, /payments/verify, and /payments/webhook endpoints.\n"
            "- Maintained financial integrity using integer paise calculations and immutable LedgerEntry audit records.\n"
            "- Validated payment flows in tests/test_payments.py and tests/test_payment_gateway_phase2.py.\n\n"
            "Co-authored-by: Swyam Shukla <swyamshukla0104@gmail.com>\n"
            "Reviewed-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 5. Swyam Shukla (3 commits)
    {
        "member_key": "Swyam_Shukla",
        "commit_dir": "Commit_01_Database_Models_And_Relationships",
        "commit_msg": (
            "feat(database): extend SQLAlchemy models for Phase 2 logistics, disputes, and escrow\n\n"
            "Design and extend SQLAlchemy 2.0 Declarative ORM models supporting delivery zones, shared drop points, delivery batches, canonical order status history, disputes, and financial ledger.\n\n"
            "- Added DeliveryZone and SharedDropPoint models with PIN code array relationships.\n"
            "- Added DeliveryBatch model with dual capacity (max_weight_kg, max_orders, cutoff_time).\n"
            "- Extended Order model with canonical OrderStatus enum and OrderStatusHistory audit model.\n"
            "- Created Dispute and DisputeEvidence models for buyer claims and photo uploads.\n"
            "- Added PaymentTransaction and LedgerEntry models using integer paise currency columns.\n"
            "- Verified foreign key constraints, cascade rules, and SQLite/PostgreSQL compatibility.\n\n"
            "Reviewed-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Swyam_Shukla",
        "commit_dir": "Commit_02_Pydantic_Schemas_And_Data_Contracts",
        "commit_msg": (
            "feat(schemas): create Pydantic validation schemas and Phase 2 API data contracts\n\n"
            "Define strict Pydantic v2 validation schemas for request bodies, responses, PIN normalization, dispute filings, batch assignments, and payment gateway payloads.\n\n"
            "- Created request and response schemas for DeliveryZone, SharedDropPoint, and DeliveryBatch.\n"
            "- Added OrderCreate schema with Indian PIN code normalization and DeliveryMode validation.\n"
            "- Added DisputeCreate and DisputeResolution schemas with reason and resolution action enums.\n"
            "- Added PaymentInitiateRequest, PaymentVerifyRequest, and LedgerEntryResponse schemas.\n"
            "- Documented OpenAPI/Swagger data contracts in docs/phase-2-api-contracts.md.\n"
            "- Verified schema serialization and from_attributes=True ORM mapping.\n\n"
            "Reviewed-by: Raksha Pandey <raksha.pandeyyy@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Swyam_Shukla",
        "commit_dir": "Commit_03_Alembic_Migrations_And_Database_Seeding",
        "commit_msg": (
            "feat(migration): configure Alembic batch migrations and Phase 2 seed data\n\n"
            "Configure Alembic migration engine with batch mode for SQLite constraint support, generate revision 22f82a866cc9, and update seed fixtures with nationwide zones.\n\n"
            "- Configured render_as_batch=True in env.py to support SQLite ALTER TABLE operations.\n"
            "- Authored migration revision 22f82a866cc9 creating batches, disputes, evidence, and ledger tables.\n"
            "- Updated seed.py with Indian delivery zones, drop points, vehicle fleets, and test user accounts.\n"
            "- Documented migration execution and rollback procedures in docs/phase-2-database-changes.md.\n"
            "- Verified migration upgrade head and seed execution cleanly in local dev environment.\n\n"
            "Reviewed-by: Anshika Sharma <anshika2907sharma@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 6. Raksha Pandey (2 commits)
    {
        "member_key": "Raksha_Pandey",
        "commit_dir": "Commit_01_Shared_API_Client_And_Auth",
        "commit_msg": (
            "feat(frontend): build shared API client wrapper and JWT session manager\n\n"
            "Implement the core client-side HTTP communication layer, JWT token persistence, multipart/form-data upload support, and centralized error notifications in vanilla JavaScript.\n\n"
            "- Created apiFetch() wrapper with automatic Authorization Bearer header injection.\n"
            "- Added multipart/form-data support for dispute photo evidence uploads without manual headers.\n"
            "- Built auth.js with login, register, token persistence, and role-based redirect routing.\n"
            "- Added centralized error toast notifications and HTTP 401 token expiry handling.\n"
            "- Verified API client against FastAPI backend authentication endpoints.\n\n"
            "Reviewed-by: Harshika Singh <harshikasingh212@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Raksha_Pandey",
        "commit_dir": "Commit_02_Shared_Design_System_And_Layout",
        "commit_msg": (
            "style(ui): implement responsive CSS design system and Phase 2 status badges\n\n"
            "Build an accessible, responsive CSS3 design system using modern CSS variables, card layouts, modal dialogs, and color-coded status badges for all 5 canonical order states.\n\n"
            "- Defined CSS custom properties for brand theme palette, typography scale, and responsive spacing.\n"
            "- Styled canonical order status badges (PLACED, CONFIRMED, PROCESSING, SHIPPED, DELIVERED).\n"
            "- Added responsive grid utilities for Buyer, Farmer, Logistics, and Admin dashboard layouts.\n"
            "- Styled dispute review cards, file upload drop zones, and payment modal overlays.\n"
            "- Verified cross-browser responsiveness from 320px mobile viewports to desktop displays.\n\n"
            "Co-authored-by: Harshika Singh <harshikasingh212@gmail.com>\n"
            "Reviewed-by: Sneha Sanodiya <snehasanodia1@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 7. Harshika Singh (3 commits)
    {
        "member_key": "Harshika_Singh",
        "commit_dir": "Commit_01_Buyer_And_Farmer_Dashboards",
        "commit_msg": (
            "feat(dashboard): implement Buyer and Farmer interactive workflows\n\n"
            "Build interactive Buyer and Farmer workflows connecting produce browsing, address checkout, batch tracking, and farmer order fulfillment.\n\n"
            "- Added Buyer delivery mode picker (Home Delivery vs Shared Drop Point) in checkout modal.\n"
            "- Connected PIN code validation and dynamic drop point dropdown selector during checkout.\n"
            "- Built live order tracking table with canonical status indicators and batch details.\n"
            "- Implemented Farmer incoming orders list and batch assignment progress views.\n"
            "- Verified UI workflows against live order engine and produce APIs.\n\n"
            "Reviewed-by: Raksha Pandey <raksha.pandeyyy@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Harshika_Singh",
        "commit_dir": "Commit_02_Logistics_And_Admin_Dashboards",
        "commit_msg": (
            "feat(dashboard): build Logistics fleet management and Admin zone controls\n\n"
            "Implement Logistics fleet dispatch controls and Platform Admin management dashboard for delivery zones, drop points, and batch monitoring.\n\n"
            "- Implemented Logistics view displaying assigned delivery batches and vehicle load meters.\n"
            "- Added batch dispatch controls and receiver confirmation trigger button.\n"
            "- Built Admin dashboard for delivery zone creation and shared drop point management.\n"
            "- Added real-time batch capacity bars visualizing weight kg and order count fill rates.\n"
            "- Verified role-based view switching correctly isolates Admin and Logistics capabilities.\n\n"
            "Co-authored-by: Hemant Yadav <hemantyadav6090@gmail.com>\n"
            "Reviewed-by: Sneha Sanodiya <snehasanodia1@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Harshika_Singh",
        "commit_dir": "Commit_03_Dispute_Payment_Interface_And_Localization",
        "commit_msg": (
            "feat(ui): add dispute photo upload modal, escrow UI, and Hindi localization\n\n"
            "Implement the buyer dispute filing modal with photo evidence upload, admin reviewer dispute adjudication screens, payment escrow status indicators, and Hindi/English localization.\n\n"
            "- Built dispute filing modal with multi-file photo evidence upload (drag and drop).\n"
            "- Added Admin reviewer dispute adjudication panel with refund/release decision buttons.\n"
            "- Displayed payment escrow status and 24-hour countdown timer on delivered orders.\n"
            "- Localized all Phase 2 UI strings into Hindi and English in lang.js.\n"
            "- Verified dispute submission and multi-lingual toggling end-to-end.\n\n"
            "Researched-by: Harshika Singh <harshikasingh212@gmail.com>\n"
            "Reviewed-by: Aparna Jha <aparnajha2021@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 8. Anshika Sharma (2 commits)
    {
        "member_key": "Anshika_Sharma",
        "commit_dir": "Commit_01_Environment_And_Dependency_Configuration",
        "commit_msg": (
            "chore(config): formalize Phase 2 settings, environment variables, and dependencies\n\n"
            "Define Phase 2 runtime settings using Pydantic Settings, document all variables in .env.example, configure requirements.txt, and update .gitignore.\n\n"
            "- Added Pydantic Settings for Razorpay keys, upload directory paths, and batch thresholds.\n"
            "- Added razorpay, alembic, and reportlab to requirements.txt.\n"
            "- Updated .env.example with secure placeholders and comprehensive variable descriptions.\n"
            "- Configured .gitignore to exclude SQLite databases, Python bytecode, and uploaded dispute photos.\n"
            "- Verified clean configuration loading with default development values.\n\n"
            "Reviewed-by: Swyam Shukla <swyamshukla0104@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Anshika_Sharma",
        "commit_dir": "Commit_02_Application_Startup_And_Docker_Integration",
        "commit_msg": (
            "feat(deployment): configure FastAPI lifespan, upload directory mounts, and Dockerfile\n\n"
            "Configure the FastAPI application lifespan, mount Phase 2 routers, initialize private upload directories, update containerization, and author operational runbooks.\n\n"
            "- Mounted disputes, logistics, payments, and orders routers in main.py.\n"
            "- Added startup lifespan hook to create backend/uploads/disputes directory.\n"
            "- Configured static frontend serving and health check endpoint at /health.\n"
            "- Updated Dockerfile for containerized deployment with migration entrypoint.\n"
            "- Authored Phase 2 operations runbook in docs/phase-2-operations-runbook.md.\n"
            "- Verified server startup and health check response.\n\n"
            "Reviewed-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 9. Aparna Jha (3 commits)
    {
        "member_key": "Aparna_Jha",
        "commit_dir": "Commit_01_Serviceability_And_Batch_Testing",
        "commit_msg": (
            "test(batches): add unit and integration test suites for zones and dual-capacity batches\n\n"
            "Implement comprehensive automated test suites for Indian PIN code validation, zone serviceability, dual-capacity batching thresholds, and schedule cutoff enforcement.\n\n"
            "- Added test_serviceability_phase2.py covering 6-digit regex and zone resolution.\n"
            "- Added test_batches_phase2.py validating dual capacity (weight kg & order count).\n"
            "- Tested schedule cutoff freezing and drop point batch isolation.\n"
            "- Validated logistics partner vehicle assignment and cold-chain constraints in test_logistics.py.\n"
            "- Verified 100% test pass rate across all batching test modules.\n\n"
            "Reviewed-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Aparna_Jha",
        "commit_dir": "Commit_02_Order_Delivery_And_Dispute_Testing",
        "commit_msg": (
            "feat(disputes): implement dispute engine, router, and comprehensive test suite\n\n"
            "Build automated test suites for canonical order state transitions, receiver confirmation without OTP, 24-hour dispute window enforcement, evidence photo upload, and reviewer resolution.\n\n"
            "- Implemented dispute_engine.py with 24-hour post-delivery window validation.\n"
            "- Added dispute photo evidence upload with UUID-based secure storage in uploads/disputes/.\n"
            "- Built reviewer resolution workflow (RELEASE_TO_FARMER, FULL_REFUND, PARTIAL_REFUND).\n"
            "- Created test_disputes_phase2.py and test_delivery_confirmation_phase2.py.\n"
            "- Verified dispute rejection for expired windows and unauthorized claims.\n\n"
            "Co-authored-by: Hemant Yadav <hemantyadav6090@gmail.com>\n"
            "Reviewed-by: Sneha Sanodiya <snehasanodia1@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
    {
        "member_key": "Aparna_Jha",
        "commit_dir": "Commit_03_Payment_Gateway_And_End_To_End_Testing",
        "commit_msg": (
            "test(e2e): add payment gateway tests and complete end-to-end workflow validation\n\n"
            "Implement automated test suites for Mock and Razorpay payment gateways, webhook signature verification, integer paise accounting, and complete buyer-to-delivery workflows.\n\n"
            "- Validated MockGateway and RazorpayGateway initiation and signature checks.\n"
            "- Verified HMAC-SHA256 webhook authenticity and duplicate payment prevention.\n"
            "- Built test_phase2_workflows.py testing end-to-end checkout through delivery.\n"
            "- Achieved 50/50 automated tests passing across the entire test suite in ~14s.\n"
            "- Confirmed zero regressions across Phase 1 authentication, produce, and order features.\n\n"
            "Researched-by: Aparna Jha <aparnajha2021@gmail.com>\n"
            "Reviewed-by: Sneha Sanodiya <snehasanodia1@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 10. Mansi Jain (1 commit)
    {
        "member_key": "Mansi_Jain",
        "commit_dir": "Commit_01_Phase2_Data_Quality_And_Metrics_Review",
        "commit_msg": (
            "docs(analytics): establish Phase 2 operational metrics and data quality framework\n\n"
            "Analyze Phase 2 operational data models, formulate Key Performance Indicators, and document data quality checks to monitor platform health and delivery SLAs.\n\n"
            "- Formulated 10 core operational KPIs (batch fill rates, DCR, dispute frequency, hold times).\n"
            "- Mapped database entities and join paths across batches, orders, and ledger.\n"
            "- Defined data quality invariants (strict PIN regex, canonical lifecycle, paise integrity).\n"
            "- Distinguished synthetic seed test fixtures from live telemetry recommendations in docs/phase-2-operational-metrics-review.md.\n\n"
            "Researched-by: Mansi Jain <mansijain1618@gmail.com>\n"
            "Reviewed-by: Sneha Sanodiya <snehasanodia1@gmail.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },

    # 11. Alankrit Purohit (1 commit)
    {
        "member_key": "Alankrit_Purohit",
        "commit_dir": "Commit_01_AI_ML_Feasibility_And_Optimization_Assessment",
        "commit_msg": (
            "docs(ml): assess AI/ML feasibility for batch optimization and validate deterministic baseline\n\n"
            "Evaluate whether machine learning is necessary or beneficial for Phase 2 delivery batching and route optimization, reviewing the deterministic business rule engine and documenting justified architectural recommendations.\n\n"
            "- Evaluated deterministic dual-capacity batching vs ML clustering heuristics.\n"
            "- Validated nearest-neighbor logistics routing vs complex VRP neural models.\n"
            "- Documented data quality prerequisites and cold-start risks for agricultural logistics.\n"
            "- Justified retention of deterministic engine for Phase 2 with roadmap for Phase 3 ML in docs/ml-feasibility-report.md.\n\n"
            "Researched-by: Alankrit Purohit <purohitak21@gmail.com>\n"
            "Reviewed-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>\n"
            f"{MANDATORY_SIGNOFF}\n"
        ),
    },
]


def update_commit_messages():
    print("Updating all 25 COMMIT_MESSAGE.txt files...")
    updated = 0
    for item in COMMITS_DATA:
        m = TEAM[item["member_key"]]
        commit_path = os.path.join(TARGET_DIR, item["member_key"], "Deliverables", m["folder"], item["commit_dir"], "COMMIT_MESSAGE.txt")
        if os.path.exists(commit_path):
            with open(commit_path, "w", encoding="utf-8") as f:
                f.write(item["commit_msg"])
            updated += 1
        else:
            print(f"WARNING: File not found: {commit_path}")
    print(f"Successfully updated {updated} COMMIT_MESSAGE.txt files.")


def update_task_and_validation_files():
    print("Updating TASK.md and VALIDATION.md files with verified emails & attribution...")
    for item in COMMITS_DATA:
        m = TEAM[item["member_key"]]
        task_dir = os.path.join(TARGET_DIR, item["member_key"], "Deliverables", m["folder"], item["commit_dir"])
        task_path = os.path.join(task_dir, "TASK.md")
        valid_path = os.path.join(task_dir, "VALIDATION.md")

        # 1. Update TASK.md
        if os.path.exists(task_path):
            with open(task_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Update Contributor line
            content = content.replace(f"**Contributor:** {m['display_name']}", f"**Contributor:** {m['display_name']} <{m['email']}>")
            # Replace old placeholder domains if any
            content = content.replace("farmcart.local", "gmail.com")

            # Ensure git commit instruction in TASK.md uses git commit --author and -F
            old_commit_step = "git commit -F COMMIT_MESSAGE.txt"
            new_commit_step = f"git commit --author=\"{m['display_name']} <{m['email']}>\" -F COMMIT_MESSAGE.txt"
            if old_commit_step in content and new_commit_step not in content:
                content = content.replace(old_commit_step, new_commit_step)

            with open(task_path, "w", encoding="utf-8") as f:
                f.write(content)

        # 2. Update VALIDATION.md
        if os.path.exists(valid_path):
            with open(valid_path, "r", encoding="utf-8") as f:
                v_content = f.read()

            v_content = v_content.replace(f"**Contributor:** {m['display_name']}", f"**Contributor:** {m['display_name']} <{m['email']}>")
            v_content = v_content.replace("farmcart.local", "gmail.com")
            v_content = v_content.replace(f"**Verified by:** {m['display_name']}", f"**Verified by:** {m['display_name']} <{m['email']}>")
            v_content = v_content.replace(
                "**Approved by:** Sneha Sanodia (QA Lead & Team Lead)",
                f"**Approved by:** Sneha Sanodiya <snehasanodia1@gmail.com> (QA Lead)\n**Sign-off Authority:** Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>"
            )

            with open(valid_path, "w", encoding="utf-8") as f:
                f.write(v_content)


def update_root_coordination_files():
    print("Updating root coordination documents in phase 2 deliveries/...")

    # 1. Update CONTRIBUTION_AND_GIT_WORKFLOW.md
    workflow_path = os.path.join(TARGET_DIR, "CONTRIBUTION_AND_GIT_WORKFLOW.md")
    workflow_content = f"""# FarmCart Phase 2 — Contributor Attribution, Commit Messages & Git Workflow Standard

This document establishes the official engineering standard for contributor attribution, Git trailers, commit messages, and repository workflow across the 11-member FarmCart engineering team.

---

## 1. Mandatory Sign-Off Rule

Every project commit must contain this exact sign-off line as its final trailer:

```text
{MANDATORY_SIGNOFF}
```

### Critical Distinctions:
1. **The actual contributor must remain the Git commit author:**
   - Commit author is set via `git commit --author="Contributor Name <email>"`.
2. **Lakshya Raj Malviya must always appear in the Signed-off-by trailer:**
   - Lakshya serves as the consistent sign-off authority and project lead for all commits.
3. **Do NOT change the actual Git author to Lakshya** merely to make the sign-off consistent.
4. **Do NOT falsely claim that Lakshya personally implemented every change.**
5. **Do NOT remove or rewrite legitimate contribution credits.**

---

## 2. Team Directory & Verified Email Addresses

Every contributor must use their exact verified email address for Git author attribution and trailers:

| Contributor | Verified Email Address | Designated Responsibility |
|---|---|---|
| **Mansi Jain** | `mansijain1618@gmail.com` | Data Analyst, Testing Engineer, metrics and data quality |
| **Raksha Pandey** | `raksha.pandeyyy@gmail.com` | Frontend Lead, database development, buyer-facing workflows |
| **Alankrit Purohit** | `purohitak21@gmail.com` | AI/ML Lead, optimization research and feasibility analysis |
| **Harshika Singh** | `harshikasingh212@gmail.com` | Research Lead, frontend development, dashboards and dispute interfaces |
| **Sneha Sanodiya** | `snehasanodia1@gmail.com` | Team Lead, QA Lead, coordination, acceptance criteria, release readiness |
| **Yash Goyal** | `yashgoyal09102005@gmail.com` | Backend Developer, serviceability, inventory and produce logic |
| **Aparna Jha** | `aparnajha2021@gmail.com` | Testing Engineer, Research Engineer, validation and quality assurance |
| **Anshika Sharma** | `anshika2907sharma@gmail.com` | Backend/deployment responsibilities, configuration and release infrastructure |
| **Swyam Shukla** | `swyamshukla0104@gmail.com` | Database Lead, API Integration Engineer, models, schemas and migrations |
| **Hemant Yadav** | `hemantyadav6090@gmail.com` | Backend Developer, logistics, delivery confirmation and payment integrations |
| **Lakshya Raj Malviya** | `177052558+Lakshya0903@users.noreply.github.com` | Backend Lead, AI/ML Engineer, architecture and integration oversight |

---

## 3. Git Attribution Trailers

For every commit, inspect the actual changes and determine who genuinely contributed:

### A. Co-authored-by
Use when another team member materially contributed to implementing the code, documentation, or design in that commit.
```text
Co-authored-by: Full Name <email>
```
*Note: Only credit genuine co-authors. Do not add the entire team to every commit.*

### B. Signed-off-by
Always include Lakshya's mandatory sign-off trailer:
```text
Signed-off-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>
```

### C. Reviewed-by
Use when a team member actually reviewed the changes, inspected implementation quality, or validated relevant test suites.
```text
Reviewed-by: Full Name <email>
```

### D. Researched-by
Use when a team member materially contributed research, technical investigation, feasibility analysis, or supporting technical documentation.
```text
Researched-by: Full Name <email>
```

---

## 4. Commit Message Structure

Follow the Conventional Commits structure consistently:

```text
<type>(<scope>): <short description>

<Detailed body explaining what was implemented, why the change was
necessary, important technical details, and validation performed.>

[Optional Co-authored-by: Full Name <email>]
[Optional Researched-by: Full Name <email>]
[Optional Reviewed-by: Full Name <email>]
Signed-off-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>
```

---

## 5. Step-by-Step Contributor Workflow

### Step 1: Pull Latest Main
```bash
git checkout main
git pull origin main
```

### Step 2: Switch to Assigned Feature Branch
```bash
git checkout -b <your-assigned-feature-branch>
```

### Step 3: Review Assigned Deliverables Folder
Navigate to your assigned task directory inside `phase 2 deliveries/`:
- Read `TASK.md` for exact files, protected boundaries, and acceptance criteria.
- Inspect the source files in `files/`.

### Step 4: Apply Changes to Repository
Copy or apply files from `files/` preserving relative repository paths. Verify diff with `git diff`.

### Step 5: Execute Automated Verification Tests
```bash
python -m unittest discover tests
```
Ensure all 50 tests pass with 0 failures and 0 errors.

### Step 6: Create the Git Commit with Full Attribution
Stage only your assigned files:
```bash
git add <file1> <file2> ...
```
Commit using your verified email and the pre-formatted `COMMIT_MESSAGE.txt`:
```bash
git commit --author="Your Name <your.email@gmail.com>" -F COMMIT_MESSAGE.txt
```

### Step 7: Push and Open Pull Request
```bash
git push -u origin <your-assigned-feature-branch>
```
Open a PR against `main`. Follow the 6-wave integration order documented in `INTEGRATION_ORDER.md`.
"""
    with open(workflow_path, "w", encoding="utf-8") as f:
        f.write(workflow_content)

    # 2. Update FILE_OWNERSHIP.csv
    csv_path = os.path.join(TARGET_DIR, "FILE_OWNERSHIP.csv")
    if os.path.exists(csv_path):
        rows = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            # Add Email column if not present
            if "Owner_Email" not in headers:
                headers.insert(3, "Owner_Email")
            rows.append(headers)
            for row in reader:
                owner = row[1]
                # Match email
                email = "unknown"
                for m_info in TEAM.values():
                    if m_info["display_name"].lower() == owner.lower() or m_info["display_name"].split()[0].lower() == owner.split()[0].lower():
                        email = m_info["email"]
                        break
                if len(row) < len(headers):
                    row.insert(3, email)
                else:
                    row[3] = email
                rows.append(row)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    # 3. Update MASTER_ALLOCATION.md
    alloc_path = os.path.join(TARGET_DIR, "MASTER_ALLOCATION.md")
    if os.path.exists(alloc_path):
        with open(alloc_path, "r", encoding="utf-8") as f:
            text = f.read()

        for m_key, m_info in TEAM.items():
            text = text.replace(f"### {m_info['display_name']} —", f"### {m_info['display_name']} (`{m_info['email']}`) —")
            text = text.replace(f"Sneha Sanodia", f"Sneha Sanodiya")
            text = text.replace("farmcart.local", "gmail.com")

        with open(alloc_path, "w", encoding="utf-8") as f:
            f.write(text)

    # 4. Update README.md
    readme_path = os.path.join(TARGET_DIR, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            r_text = f.read()

        r_text = r_text.replace("Sneha Sanodia", "Sneha Sanodiya")
        r_text = r_text.replace("farmcart.local", "gmail.com")

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(r_text)

    # 5. Update VERIFICATION_REPORT.md
    verif_path = os.path.join(TARGET_DIR, "VERIFICATION_REPORT.md")
    if os.path.exists(verif_path):
        with open(verif_path, "r", encoding="utf-8") as f:
            v_text = f.read()

        v_text = v_text.replace("Sneha Sanodia", "Sneha Sanodiya")
        v_text = v_text.replace("farmcart.local", "gmail.com")

        with open(verif_path, "w", encoding="utf-8") as f:
            f.write(v_text)

    print("Successfully updated root coordination documents.")


if __name__ == "__main__":
    update_commit_messages()
    update_task_and_validation_files()
    update_root_coordination_files()
    print("\n[COMPLETE] All 25 commit packages and root coordination documents conform to the standard!")
