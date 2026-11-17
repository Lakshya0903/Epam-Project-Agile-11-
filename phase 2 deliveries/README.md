# FarmCart Phase 2 — 11-Member Contribution Distribution Packages

**Project:** FarmCart — Direct Farm-to-Consumer Marketplace  
**Team:** Agile 11  
**Target Stage:** Phase 2 Complete (Nationwide Logistics, Batches, Disputes & Gateways)  
**Verification:** 50 / 50 Passing Automated Tests (100% Pass Rate)  

---

## 1. Overview & Purpose

This directory contains the complete, structured work-allocation breakdown of the completed FarmCart Phase 2 application across all **11 team members**. Rather than an arbitrary dump of files, every single contribution has been mapped to the respective engineer's domain responsibility and organized into sequential, reviewable **commit task folders**.

Every member's package contains:
- `TASK.md`: Detailed engineering specification, files involved, protected boundaries, dependencies, and acceptance criteria.
- `COMMIT_MESSAGE.txt`: Conventional, descriptive proposed git commit message.
- `VALIDATION.md`: Exact verification steps, test commands, and quality sign-off checklist.
- `files/`: The exact source code payload preserving repository-relative paths.

---

## 2. Master Team Roster & Allocation Summary

| # | Contributor | Role | Commit Tasks | Primary Modules |
|---|---|---|:---:|---|
| 1 | **Sneha Sanodiya** | Team Lead + QA Lead | 2 | Baseline audit, architecture, security review, release readiness |
| 2 | **Lakshya Raj Malviya** | Backend Lead + AI/ML Engineer | 3 | Order engine, 5-state lifecycle, dual-capacity batch engine, checkout |
| 3 | **Yash Goyal** | Backend Developer | 2 | Nationwide PIN validation, serviceability engine, produce inventory |
| 4 | **Hemant Yadav** | Backend Developer 3 | 3 | Logistics APIs, receiver delivery confirm without OTP, payment gateways |
| 5 | **Swyam Shukla** | Database Lead + API Integration 1 | 3 | SQLAlchemy models, Pydantic v2 schemas, Alembic batch migrations |
| 6 | **Raksha Pandey** | Frontend Lead + Database Developer 1 | 2 | Shared API client, JWT auth wrapper, responsive CSS design system |
| 7 | **Harshika Singh** | Research Lead + Frontend Developer 2 | 3 | Buyer & Farmer dashboards, Logistics & Admin views, dispute UI, Hindi |
| 8 | **Anshika Sharma** | Backend Developer 1 + Deployment Mgr | 2 | Environment settings, dependencies, Dockerfile, lifespan startup |
| 9 | **Aparna Jha** | Testing Engineer + Research Engineer | 3 | Automated test suites (batches, disputes, payment gateways, E2E) |
| 10 | **Mansi Jain** | Data Analyst + Testing Engineer | 1 | Operational metrics review, KPI formulations, data quality |
| 11 | **Alankrit Purohit** | AI/ML Lead | 1 | AI/ML feasibility study, batch optimization evaluation |
| **TOTAL** | **11 Members** | **Complete Engineering Team** | **25 Commits** | **86 Tracked Files (100% Phase 2 Coverage)** |

---

## 3. Root Coordination Artifacts

- **[`MASTER_ALLOCATION.md`](./MASTER_ALLOCATION.md)**: Exhaustive breakdown of every member, task, file payload, and dependency.
- **[`FILE_OWNERSHIP.csv`](./FILE_OWNERSHIP.csv)**: Definitive file-by-file ownership matrix preventing merge conflicts.
- **[`COMMIT_DEPENDENCY_MAP.md`](./COMMIT_DEPENDENCY_MAP.md)**: Dependency graph illustrating the strict technical sequence across tasks.
- **[`INTEGRATION_ORDER.md`](./INTEGRATION_ORDER.md)**: Step-by-step branch integration order for git merges.
- **[`CONTRIBUTION_AND_GIT_WORKFLOW.md`](./CONTRIBUTION_AND_GIT_WORKFLOW.md)**: Standard operating procedure for contributors applying and committing their tasks.
- **[`VERIFICATION_REPORT.md`](./VERIFICATION_REPORT.md)**: Verification audit proving zero missing files and 100% test pass status.
