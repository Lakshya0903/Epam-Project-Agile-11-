# Task Specification: Nationwide Indian PIN Code Serviceability Engine

**Commit / Task Identifier:** `Commit_01_Nationwide_Serviceability_Engine`  
**Sequence Number:** Commit 01  
**Contributor:** Yash Goyal <yashgoyal09102005@gmail.com>  
**Role:** Backend Developer  
**Assigned Git Branch:** `feature/phase2-yash-serviceability`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Implement nationwide Indian PIN code validation, delivery zone mapping, and delivery mode eligibility evaluation (home delivery vs shared drop points).

---

## 2. Technical Background & Existing Context

FarmCart must support address capture across all Indian states and union territories, while restricting delivery checkout only to active serviceable zones with valid delivery fleets.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `backend/app/services/serviceability_engine.py`
- `backend/app/utils/geo.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/models.py (Coordinate DeliveryZone model with Swyam)`
- `backend/app/routers/orders.py (Consumed by Lakshya)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Swyam Shukla's DeliveryZone and SharedDropPoint ORM models.

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
python -m unittest tests/test_serviceability_phase2.py
```

---

## 8. Acceptance Criteria

- [ ] Invalid PIN codes (letters, 5 digits, leading zeros) fail validation
- [ ] PIN with spaces ('560 038') sanitized and validated correctly
- [ ] Unconfigured PIN codes return serviceable=False with actionable reason text

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-yash-serviceability
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_01_Nationwide_Serviceability_Engine`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
