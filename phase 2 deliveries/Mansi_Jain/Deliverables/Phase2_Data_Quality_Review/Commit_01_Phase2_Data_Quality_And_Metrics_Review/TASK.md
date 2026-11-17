# Task Specification: Phase 2 Operational Reporting, Data Quality and KPI Formulations

**Commit / Task Identifier:** `Commit_01_Phase2_Data_Quality_And_Metrics_Review`  
**Sequence Number:** Commit 01  
**Contributor:** Mansi Jain <mansijain1618@gmail.com>  
**Role:** Data Analyst + Testing Engineer  
**Assigned Git Branch:** `feature/phase2-mansi-metrics`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Analyze Phase 2 operational data models, formulate Key Performance Indicators (batch fill rate, cutoff misses, delivery delay, dispute latency, escrow hold time), and document data quality checks.

---

## 2. Technical Background & Existing Context

FarmCart Phase 2 introduces multi-dimensional operational data across batches, drop points, deliveries, disputes, and escrow ledgers. A formalized operational reporting review is required to guide production monitoring.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `docs/phase-2-operational-metrics-review.md`
- `analytics/data_quality.py`
- `analytics/mandi_analysis.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/models.py (Owned by Swyam)`
- `backend/app/services/payment_engine.py (Owned by Hemant)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Swyam Shukla's data models and database changes.

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
python -c "import analytics.data_quality; print('Data quality module verified!')"
```

---

## 8. Acceptance Criteria

- [ ] Operational metrics report completed in docs/phase-2-operational-metrics-review.md
- [ ] All 10 KPIs include rigorous mathematical formulas and source table mappings
- [ ] Actionable operational recommendations provided for batch watchers and escrow jobs

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-mansi-metrics
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_01_Phase2_Data_Quality_And_Metrics_Review`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
