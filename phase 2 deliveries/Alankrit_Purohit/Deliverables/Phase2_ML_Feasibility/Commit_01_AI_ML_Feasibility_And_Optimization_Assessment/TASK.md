# Task Specification: Phase 2 AI/ML Feasibility Assessment and Optimization Study

**Commit / Task Identifier:** `Commit_01_AI_ML_Feasibility_And_Optimization_Assessment`  
**Sequence Number:** Commit 01  
**Contributor:** Alankrit Purohit <purohitak21@gmail.com>  
**Role:** AI/ML Lead  
**Assigned Git Branch:** `feature/phase2-alankrit-ml-review`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Evaluate whether machine learning is necessary or beneficial for Phase 2 delivery batching and route optimization, review the deterministic business rule engine, and document justified architectural recommendations.

---

## 2. Technical Background & Existing Context

Engineering rigor requires evaluating when ML provides tangible value vs when deterministic rules are superior. For Phase 2, deterministic area/capacity batching provides 100% auditability, zero inference latency, and no cold-start failure risks.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `docs/ml-feasibility-report.md`
- `ml/README.md`
- `ml/evaluation.py`
- `ml/price_predictor.py`
- `ml/experiments/baseline_experiment.py`
- `ml/experiments/dataset_generator.py`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `backend/app/services/batch_engine.py (Owned by Lakshya)`
- `backend/app/services/logistics_engine.py (Owned by Hemant)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Lakshya's batch_engine and Hemant's logistics_engine.

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
python ml/evaluation.py
```

---

## 8. Acceptance Criteria

- [ ] Feasibility report thoroughly assesses batching and logistics optimization
- [ ] Justified recommendation explains why deterministic logic is optimal for Phase 2
- [ ] Phase 3 ML roadmap defined with required data schemas and training objectives

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-alankrit-ml-review
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_01_AI_ML_Feasibility_And_Optimization_Assessment`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
