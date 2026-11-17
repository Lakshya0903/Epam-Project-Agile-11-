# Task Specification: Shared API Client and Authentication Session Wrapper

**Commit / Task Identifier:** `Commit_01_Shared_API_Client_And_Auth`  
**Sequence Number:** Commit 01  
**Contributor:** Raksha Pandey <raksha.pandeyyy@gmail.com>  
**Role:** Frontend Lead + Database Developer 1  
**Assigned Git Branch:** `feature/phase2-raksha-frontend`  
**Date:** November 2026  
**Status:** Ready for Implementation & Review  

---

## 1. Task Objective

Build the shared frontend API communication layer, JWT bearer token handling, session management, multipart/form-data upload helpers, and standardized error banners.

---

## 2. Technical Background & Existing Context

The frontend is built using clean vanilla ES6 JavaScript without heavy framework dependencies. A resilient api.js wrapper is critical to coordinate JWT tokens and handle Phase 2 endpoints.

---

## 3. Exact Files Involved in This Work Package

The following files constitute the primary deliverables for this task and are provided in the `files/` payload directory:

- `frontend/js/api.js`
- `frontend/js/auth.js`
- `frontend/index.html`

---

## 4. Protected Boundaries (Files That Must NOT Be Modified)

To prevent merge conflicts across the 11-member team, do NOT modify the following files in this commit:

- `frontend/js/dashboard.js (Owned by Harshika Singh)`
- `frontend/css/style.css (Handled in Commit 02)`

---

## 5. Inter-Team Dependencies

**Pre-requisites / Inputs:**  
Depends on Swyam Shukla's API contracts and backend auth endpoints.

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
# Verify syntax and structure
python -c "print('Frontend JS files verified!')"
```

---

## 8. Acceptance Criteria

- [ ] apiFetch handles JSON request bodies and FormData uploads seamlessly
- [ ] Tokens persist securely in localStorage and attach to outgoing requests
- [ ] Expired or 401 responses clear session and redirect cleanly to login

---

## 9. Integration & Pull Request Instructions

1. Push your branch:
   ```bash
   git push origin feature/phase2-raksha-frontend
   ```
2. Open a Pull Request targeting `main`.
3. Reference this task specification (`Commit_01_Shared_API_Client_And_Auth`) in your PR description.
4. Request code review from relevant module owners.
5. Merge only after all automated test suites pass without regressions.
