# Task Specification: Buyer and Farmer Dashboard User Workflows

**Commit / Task Identifier:** `Commit_01_Buyer_And_Farmer_Dashboards`  
**Sequence Number:** Commit 01  
**Contributor:** Harshika Singh <harshikasingh212@gmail.com>  
**Role:** Research Lead + Frontend Developer 2  
**Assigned Git Branch:** `feature/phase2-harshika-dashboards`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Implement interactive Buyer and Farmer workflows in dashboard.html and dashboard.js, connecting produce browsing, address checkout, order tracking, and farmer order fulfillment.

---

## 2. Technical Background & Existing Context

Buyers need seamless delivery mode selection (home delivery vs shared drop points) and order tracking. Farmers need clear visibility into incoming batch-assigned orders and fulfillment progress.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `frontend/dashboard.html`
- `frontend/js/dashboard.js`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `frontend/js/api.js (Owned by Raksha Pandey)`
- `frontend/css/style.css (Owned by Raksha Pandey)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Raksha Pandey's api.js and backend order/produce endpoints.

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

- [ ] Buyer can place order with PIN code and select delivery mode
- [ ] Farmer can view incoming orders and update fulfillment status
- [ ] Orders show assigned delivery batch and estimated delivery schedule

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-harshika-dashboards
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_01_Buyer_And_Farmer_Dashboards`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
