# Task Specification: Transactional Order Checkout and Automatic Batch Assignment

**Commit / Task Identifier:** `Commit_03_Order_Batch_Logistics_Integration`  
**Sequence Number:** Commit 03  
**Contributor:** Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>  
**Role:** Backend Lead + AI/ML Engineer  
**Assigned Git Branch:** `feature/phase2-lakshya-orders-batches`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Integrate the order router with the dual-capacity batch engine and serviceability validator to guarantee atomic order creation, inventory reservation, and batch allocation.

---

## 2. Technical Background & Existing Context

Order checkout must tie together address serviceability validation, produce inventory checks, financial calculation, and automatic batch assignment within a single database transaction.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `backend/app/routers/orders.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/routers/logistics.py (Owned by Hemant Yadav)`
- `backend/app/routers/payments.py (Owned by Hemant Yadav)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Commit 01 & 02, Yash Goyal's serviceability_engine, and Swyam Shukla's schemas.

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
python -m unittest tests/test_orders.py tests/test_batches_phase2.py
```

---

## 8. Acceptance Criteria

- [ ] POST /orders fails with HTTP 400 if destination PIN is unserviceable
- [ ] Successfully placed order has assigned batch_id and status PLACED
- [ ] Batch current_weight_kg and current_order_count increment atomically

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-lakshya-orders-batches
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_03_Order_Batch_Logistics_Integration`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
