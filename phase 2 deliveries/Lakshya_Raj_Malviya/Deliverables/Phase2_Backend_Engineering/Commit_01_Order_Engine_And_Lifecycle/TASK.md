# Task Specification: Canonical 5-State Order Lifecycle and Reservation Engine

**Commit / Task Identifier:** `Commit_01_Order_Engine_And_Lifecycle`  
**Sequence Number:** Commit 01  
**Contributor:** Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>  
**Role:** Backend Lead + AI/ML Engineer  
**Assigned Git Branch:** `feature/phase2-lakshya-orders-batches`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Implement the canonical 5-state order lifecycle (PLACED -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED), status history tracking, and inventory reservation rollback.

---

## 2. Technical Background & Existing Context

Phase 1 lacked a rigid state machine, allowing potential out-of-order state mutations. Phase 2 introduces strict state transition validation, preventing illegal jumps and ensuring inventory consistency upon cancellation.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `backend/app/services/order_engine.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/models.py (Coordinate enum changes with Swyam)`
- `backend/app/routers/orders.py (Integration occurs in Commit 03)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Swyam Shukla's OrderStatus and OrderStatusHistory models.

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
python -m unittest tests/test_orders.py
```

---

## 8. Acceptance Criteria

- [ ] Illegal state transitions raise HTTP 400 Bad Request
- [ ] Cancellation restocks produce quantities and logs cancellation history
- [ ] State changes write an immutable row to order_status_history

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-lakshya-orders-batches
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_01_Order_Engine_And_Lifecycle`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
