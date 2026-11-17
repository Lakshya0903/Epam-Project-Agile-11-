# FarmCart Phase 2 — Commit Dependency Map

This document visualizes the technical prerequisite graph across the **25 commit packages** of the 11 team members.

---

## 1. Technical Dependency Diagram (Mermaid)

```mermaid
flowchart TD
    subgraph Foundation ["Stage 0: Foundation & Schema"]
        SNEHA_01["Sneha Commit 01<br/>Baseline Audit & Architecture"]
        ANSHIKA_01["Anshika Commit 01<br/>Config & Dependencies"]
        SWYAM_01["Swyam Commit 01<br/>SQLAlchemy Models"]
        SWYAM_02["Swyam Commit 02<br/>Pydantic Schemas"]
        SWYAM_03["Swyam Commit 03<br/>Alembic Migrations & Seed"]
    end

    subgraph BackendCore ["Stage 1: Core Domain Engines"]
        YASH_01["Yash Commit 01<br/>PIN & Serviceability Engine"]
        LAKSHYA_01["Lakshya Commit 01<br/>5-State Order Engine"]
        LAKSHYA_02["Lakshya Commit 02<br/>Dual-Capacity Batch Engine"]
        YASH_02["Yash Commit 02<br/>Produce Inventory"]
        LAKSHYA_03["Lakshya Commit 03<br/>Order-Batch Checkout"]
    end

    subgraph LogisticsAndPay ["Stage 2: Logistics & Gateway Integration"]
        HEMANT_01["Hemant Commit 01<br/>Logistics & Fleet APIs"]
        HEMANT_02["Hemant Commit 02<br/>Receiver Confirm Without OTP"]
        HEMANT_03["Hemant Commit 03<br/>Payment Gateways & Ledger"]
        APARNA_02["Aparna Commit 02<br/>Dispute Engine & Tests"]
    end

    subgraph FrontendUI ["Stage 3: Frontend Presentation Tier"]
        RAKSHA_01["Raksha Commit 01<br/>Shared API Client & Auth"]
        RAKSHA_02["Raksha Commit 02<br/>CSS Design System"]
        HARSHIKA_01["Harshika Commit 01<br/>Buyer & Farmer Dashboards"]
        HARSHIKA_02["Harshika Commit 02<br/>Logistics & Admin Dashboards"]
        HARSHIKA_03["Harshika Commit 03<br/>Dispute UI & Hindi Lang"]
    end

    subgraph DeploymentAndQA ["Stage 4: Quality Assurance & Release"]
        ANSHIKA_02["Anshika Commit 02<br/>Lifespan & Dockerfile"]
        APARNA_01["Aparna Commit 01<br/>Batch & Zone Tests"]
        APARNA_03["Aparna Commit 03<br/>Gateways & E2E Tests"]
        MANSI_01["Mansi Commit 01<br/>Operational Metrics"]
        ALANKRIT_01["Alankrit Commit 01<br/>ML Feasibility Report"]
        SNEHA_02["Sneha Commit 02<br/>Release Verification (50/50 Tests)"]
    end

    SNEHA_01 --> SWYAM_01
    ANSHIKA_01 --> SWYAM_01
    SWYAM_01 --> SWYAM_02
    SWYAM_02 --> SWYAM_03

    SWYAM_01 --> YASH_01
    SWYAM_01 --> LAKSHYA_01
    SWYAM_01 --> LAKSHYA_02

    YASH_01 --> LAKSHYA_03
    LAKSHYA_01 --> LAKSHYA_03
    LAKSHYA_02 --> LAKSHYA_03
    YASH_02 --> LAKSHYA_03

    LAKSHYA_02 --> HEMANT_01
    LAKSHYA_01 --> HEMANT_02
    SWYAM_01 --> HEMANT_03
    HEMANT_02 --> APARNA_02

    SWYAM_02 --> RAKSHA_01
    RAKSHA_01 --> RAKSHA_02
    RAKSHA_01 --> HARSHIKA_01
    LAKSHYA_03 --> HARSHIKA_01
    HEMANT_01 --> HARSHIKA_02
    APARNA_02 --> HARSHIKA_03
    HEMANT_03 --> HARSHIKA_03

    LAKSHYA_02 --> APARNA_01
    HEMANT_03 --> APARNA_03
    APARNA_02 --> APARNA_03
    ANSHIKA_01 --> ANSHIKA_02

    SWYAM_01 --> MANSI_01
    LAKSHYA_02 --> ALANKRIT_01

    APARNA_03 --> SNEHA_02
    HARSHIKA_03 --> SNEHA_02
    ANSHIKA_02 --> SNEHA_02
```

---

## 2. Dependency Matrix Summary

1. **Swyam Shukla (Database Lead):** Must establish models (`Commit 01`) and schemas (`Commit 02`) before any backend service or frontend API client can serialize data.
2. **Yash Goyal (Serviceability):** Must finalize Indian PIN code validation (`Commit 01`) before Lakshya's order checkout (`Commit 03`) can validate delivery addresses.
3. **Lakshya Raj Malviya (Order & Batch Engines):** Must implement state transitions (`Commit 01`) and batch logic (`Commit 02`) before logistics dispatch or order checkout can be finalized.
4. **Hemant Yadav (Logistics & Payments):** Relies on order state transitions for receiver delivery confirmation (`Commit 02`) and Swyam's financial schema for payment gateways (`Commit 03`).
5. **Raksha Pandey (Shared Frontend):** Must deliver `apiFetch` in `api.js` before Harshika Singh can wire up buyer, farmer, and admin dashboards.
6. **Harshika Singh (Dashboards):** Directly consumes endpoints from Lakshya, Hemant, and Aparna.
7. **Aparna Jha (Testing):** Executes verification suites validating the integration of all backend and UI workflows.
8. **Sneha Sanodia (Release Readiness):** Validates the entire application once all 50 automated tests pass and certifies production release.
