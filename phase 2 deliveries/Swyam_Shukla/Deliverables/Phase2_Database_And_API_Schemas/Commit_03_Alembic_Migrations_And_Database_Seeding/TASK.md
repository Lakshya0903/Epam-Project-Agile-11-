# Task Specification: Alembic Database Migrations and Seed Data Management

**Commit / Task Identifier:** `Commit_03_Alembic_Migrations_And_Database_Seeding`  
**Sequence Number:** Commit 03  
**Contributor:** Swyam Shukla <swyamshukla0104@gmail.com>  
**Role:** Database Lead + API Integration Engineer 1  
**Assigned Git Branch:** `feature/phase2-swyam-database`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Configure Alembic batch mode migrations for SQLite/PostgreSQL compatibility, generate revision 22f82a866cc9, update seed data fixtures, and document migration runbooks.

---

## 2. Technical Background & Existing Context

SQLite does not support standard ALTER TABLE statements for foreign keys and drop column operations. Alembic must be configured with render_as_batch=True to ensure reliable schema migrations.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `backend/alembic.ini`
- `backend/alembic/README`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/22f82a866cc9_phase_2_delivery_batches_disputes_.py`
- `backend/seed.py`
- `Documents/database-migrations.md`
- `docs/phase-2-database-changes.md`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/models.py (Committed in Commit 01)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Commit 01 & 02.

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
alembic -c backend/alembic.ini upgrade head
```
```bash
python backend/seed.py
```

---

## 8. Acceptance Criteria

- [ ] Alembic upgrades to head (22f82a866cc9) cleanly without constraint errors
- [ ] seed.py executes idempotently and seeds all demo roles and locations
- [ ] Migration rollback (downgrade -1) tested and functional

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-swyam-database
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_03_Alembic_Migrations_And_Database_Seeding`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
