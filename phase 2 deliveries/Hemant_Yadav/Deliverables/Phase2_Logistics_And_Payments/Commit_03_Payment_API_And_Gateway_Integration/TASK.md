# Task Specification: Pluggable Payment Gateway Integration and Integer Paise Ledger

**Commit / Task Identifier:** `Commit_03_Payment_API_And_Gateway_Integration`  
**Sequence Number:** Commit 03  
**Contributor:** Hemant Yadav <hemantyadav6090@gmail.com>  
**Role:** Backend Developer 3  
**Assigned Git Branch:** `feature/phase2-hemant-logistics-payments`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Implement payment initiation, verification, webhook endpoints, pluggable Mock and Razorpay providers, and an immutable integer paise escrow ledger.

---

## 2. Technical Background & Existing Context

FarmCart Phase 2 requires pluggable payment gateways, integer paise arithmetic to avoid floating-point errors, HMAC signature verification, and automated escrow hold until delivery.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `backend/app/routers/payments.py`
- `backend/app/services/payment_engine.py`
- `backend/app/services/payment_gateways/__init__.py`
- `backend/app/services/payment_gateways/base.py`
- `backend/app/services/payment_gateways/mock_provider.py`
- `backend/app/services/payment_gateways/razorpay_provider.py`
- `docs/phase-2-payment-gateway.md`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/models.py (Coordinate PaymentTransaction with Swyam)`
- `backend/app/config.py (Coordinate Razorpay settings with Anshika)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Swyam Shukla's payment models/schemas and Anshika's config settings.

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
python -m unittest tests/test_payments.py tests/test_payment_gateway_phase2.py
```

---

## 8. Acceptance Criteria

- [ ] Payment initiate returns valid gateway order reference and paise amount
- [ ] Valid mock/razorpay signature transitions order to CONFIRMED and records transaction
- [ ] Invalid HMAC signature raises HTTP 400 and rejects verification

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-hemant-logistics-payments
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_03_Payment_API_And_Gateway_Integration`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
