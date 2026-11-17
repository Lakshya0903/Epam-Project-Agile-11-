# Task Specification: SQLAlchemy ORM Models and Phase 2 Relational Schema

**Commit / Task Identifier:** `Commit_01_Database_Models_And_Relationships`  
**Sequence Number:** Commit 01  
**Contributor:** Swyam Shukla <swyamshukla0104@gmail.com>  
**Role:** Database Lead + API Integration Engineer 1  
**Assigned Git Branch:** `feature/phase2-swyam-database`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Define and extend SQLAlchemy Declarative models supporting delivery zones, drop points, delivery batches, canonical order status history, disputes, evidence, and financial ledger.

---

## 2. Technical Background & Existing Context

The database foundation must support both SQLite for local development and PostgreSQL for production, using properly indexed foreign keys, constraints, and integer paise monetary columns.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `backend/app/models.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/schemas.py (Pydantic schemas handled in Commit 02)`
- `backend/alembic/ (Migrations handled in Commit 03)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
None. Foundational data schema definition for all backend services.

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
python -c "from backend.app.models import Base; print('Models imported successfully!')"
```

---

## 8. Acceptance Criteria

- [ ] All models import cleanly without circular foreign key errors
- [ ] Cascade delete and relationship back-references properly configured
- [ ] Monetary fields strictly typed as Integer (paise)

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-swyam-database
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_01_Database_Models_And_Relationships`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
