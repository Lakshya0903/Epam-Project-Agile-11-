# Task Specification: Dispute Filing Interface, Payment Status and Multi-lingual Localization

**Commit / Task Identifier:** `Commit_03_Dispute_Payment_Interface_And_Localization`  
**Sequence Number:** Commit 03  
**Contributor:** Harshika Singh <harshikasingh212@gmail.com>  
**Role:** Research Lead + Frontend Developer 2  
**Assigned Git Branch:** `feature/phase2-harshika-dashboards`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Implement the buyer dispute filing modal with photo evidence upload, admin reviewer dispute adjudication screens, payment escrow status indicators, and Hindi/English localization.

---

## 2. Technical Background & Existing Context

Buyers require an easy dispute filing flow with photo uploads within the 24h window. Reviewers need an adjudication screen. All Phase 2 UI strings must be localized in Hindi and English.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `frontend/dashboard.html`
- `frontend/js/dashboard.js`
- `frontend/js/lang.js`
- `frontend/analytics.html`
- `frontend/js/analytics.js`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/routers/disputes.py (Owned by Aparna)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Commit 01 & 02, Aparna's dispute engine, and Hemant's payment endpoints.

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
python -m unittest tests/test_disputes_phase2.py
```

---

## 8. Acceptance Criteria

- [ ] Buyer can attach image files and submit dispute within 24h window
- [ ] Reviewer can resolve dispute with release or refund action
- [ ] Language toggle seamlessly updates Phase 2 labels between English and Hindi

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-harshika-dashboards
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_03_Dispute_Payment_Interface_And_Localization`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
