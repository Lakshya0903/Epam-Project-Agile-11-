# Task Specification: Serviceability, Zone Lookup and Dual-Capacity Batch Test Suites

**Commit / Task Identifier:** `Commit_01_Serviceability_And_Batch_Testing`  
**Sequence Number:** Commit 01  
**Contributor:** Aparna Jha <aparnajha2021@gmail.com>  
**Role:** Testing Engineer + Research Engineer  
**Assigned Git Branch:** `feature/phase2-aparna-testing`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Implement comprehensive automated test suites for Indian PIN code validation, zone serviceability, dual-capacity batching thresholds, and schedule cutoff enforcement.

---

## 2. Technical Background & Existing Context

Automated verification must guarantee that invalid PIN codes are rejected, capacity overflow triggers new batch creation, and drop point orders are never mixed with home delivery batches.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `tests/test_serviceability_phase2.py`
- `tests/test_batches_phase2.py`
- `tests/test_logistics.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/services/batch_engine.py (Owned by Lakshya)`
- `backend/app/services/serviceability_engine.py (Owned by Yash)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Lakshya's batch_engine and Yash's serviceability_engine.

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
python -m unittest tests/test_serviceability_phase2.py tests/test_batches_phase2.py tests/test_logistics.py
```

---

## 8. Acceptance Criteria

- [ ] All test cases pass with 100% success rate
- [ ] Boundary conditions for max_weight_kg and max_orders covered
- [ ] Invalid PIN codes and expired cutoffs trigger expected exceptions

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-aparna-testing
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_01_Serviceability_And_Batch_Testing`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
