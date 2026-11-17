# Task Specification: Dual-Capacity Delivery Batch Engine and Schedule Cutoffs

**Commit / Task Identifier:** `Commit_02_Automatic_Batch_Engine`  
**Sequence Number:** Commit 02  
**Contributor:** Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>  
**Role:** Backend Lead + AI/ML Engineer  
**Assigned Git Branch:** `feature/phase2-lakshya-orders-batches`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Build the dynamic dual-capacity delivery batch engine that enforces both maximum weight (kg) and maximum order count limits, calculates scheduling cutoffs, and isolates drop points.

---

## 2. Technical Background & Existing Context

Phase 1 used a hardcoded 25 kg single threshold. Phase 2 requires dual constraints (weight + orders), configurable thresholds per zone, dynamic cutoff calculations, and shared drop point isolation.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `backend/app/services/batch_engine.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/models.py (Coordinate DeliveryBatch fields with Swyam)`
- `backend/app/services/serviceability_engine.py (Owned by Yash Goyal)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Swyam Shukla's DeliveryBatch model and Yash Goyal's zone serviceability logic.

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
python -m unittest tests/test_batches_phase2.py
```

---

## 8. Acceptance Criteria

- [ ] Orders exceeding max_weight_kg or max_orders spawn a new batch in the same slot
- [ ] Orders past the cutoff time are blocked from expired batches
- [ ] Drop point orders are never grouped into home delivery batches

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-lakshya-orders-batches
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_02_Automatic_Batch_Engine`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
