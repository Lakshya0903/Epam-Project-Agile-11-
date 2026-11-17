# Task Specification: Produce Inventory Management and Weight Compatibility

**Commit / Task Identifier:** `Commit_02_Produce_Inventory_Compatibility`  
**Sequence Number:** Commit 02  
**Contributor:** Yash Goyal <yashgoyal09102005@gmail.com>  
**Role:** Backend Developer  
**Assigned Git Branch:** `feature/phase2-yash-serviceability`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Update produce endpoints and produce engine to enforce quantity availability, weight consistency for batching, and preserve Phase 1 farmer listing capabilities.

---

## 2. Technical Background & Existing Context

Produce listings must provide accurate unit weights and inventory availability so the batch engine can calculate batch loads accurately.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `backend/app/routers/produce.py`
- `backend/app/services/produce_engine.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/services/order_engine.py (Owned by Lakshya)`
- `frontend/js/dashboard.js (Owned by Harshika)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Swyam Shukla's Produce and User models.

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
python -m unittest tests/test_produce.py
```

---

## 8. Acceptance Criteria

- [ ] Listing produce with 0 quantity correctly flags as sold out
- [ ] Farmer produce updates reflect immediately in available stock
- [ ] Invalid produce categories or negative prices return validation errors

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-yash-serviceability
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_02_Produce_Inventory_Compatibility`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
