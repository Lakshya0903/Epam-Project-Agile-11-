# Task Specification: Order Lifecycle, Receiver Confirmation and Dispute Subsystem

**Commit / Task Identifier:** `Commit_02_Order_Delivery_And_Dispute_Testing`  
**Sequence Number:** Commit 02  
**Contributor:** Aparna Jha <aparnajha2021@gmail.com>  
**Role:** Testing Engineer + Research Engineer  
**Assigned Git Branch:** `feature/phase2-aparna-testing`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Build automated tests for canonical order state transitions, receiver confirmation without OTP, 24-hour dispute window enforcement, evidence photo upload, and reviewer resolution.

---

## 2. Technical Background & Existing Context

Dispute resolution is a core Phase 2 requirement. This task validates that only delivered orders can be disputed within 24 hours, evidence files are securely stored, and reviewers can resolve claims.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `tests/test_orders.py`
- `tests/test_delivery_confirmation_phase2.py`
- `tests/test_disputes_phase2.py`
- `backend/app/routers/disputes.py`
- `backend/app/services/dispute_engine.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/services/payment_engine.py (Owned by Hemant)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Lakshya's order engine and Hemant's receiver confirmation.

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
python -m unittest tests/test_orders.py tests/test_delivery_confirmation_phase2.py tests/test_disputes_phase2.py
```

---

## 8. Acceptance Criteria

- [ ] Dispute filed >24h after delivery rejected with HTTP 400
- [ ] Receiver delivery confirmation transitions order to DELIVERED without OTP
- [ ] Reviewer resolution updates dispute status and triggers escrow actions

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-aparna-testing
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_02_Order_Delivery_And_Dispute_Testing`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
