# Task Specification: FastAPI Application Factory, Lifespan Hooks and Docker Setup

**Commit / Task Identifier:** `Commit_02_Application_Startup_And_Docker_Integration`  
**Sequence Number:** Commit 02  
**Contributor:** Anshika Sharma <anshika2907sharma@gmail.com>  
**Role:** Backend Developer 1 + Deployment Manager  
**Assigned Git Branch:** `feature/phase2-anshika-deployment`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Configure the FastAPI application lifespan, mount routers, configure CORS, initialize upload directories, update the Dockerfile, and document operations.

---

## 2. Technical Background & Existing Context

The application entry point main.py must mount all new Phase 2 routers (disputes, payments, logistics), ensure private upload directories exist on startup, and provide reproducible Docker build steps.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `backend/Dockerfile`
- `backend/app/main.py`
- `docs/phase-2-operations-runbook.md`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/routers/* (Routers are mounted, not modified)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Commit 01 and all API routers.

---

## 6. Detailed Implementation & Review Steps

1. **Inspect Workspace Baseline:** Confirm that your local repository branch is up-to-date with `origin/main`.
2. **Review Code Payload:** Inspect the files provided in `files/` preserving relative repository paths.
3. **Verify Boundary Conditions:** Ensure changes do not introduce unintended side effects to adjacent services.
4. **Execute Automated Verification:** Run the test commands listed in Section 7 and record outcomes in `VALIDATION.md`.
5. **Prepare Git Commit:** Use the proposed message in `COMMIT_MESSAGE.txt` as your commit text.

---

## 7. Relevant Verification Commands

Execute the following verification commands to validate this task:

```bash
python -c "from backend.app.main import app; print('FastAPI app initialized successfully!')"
```

---

## 8. Acceptance Criteria

- [ ] GET /health returns HTTP 200 with status ok and version 2.0.0
- [ ] backend/uploads/disputes directory is auto-created on application startup
- [ ] Dockerfile builds a lightweight, production-ready container image

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-anshika-deployment
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_02_Application_Startup_And_Docker_Integration`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
