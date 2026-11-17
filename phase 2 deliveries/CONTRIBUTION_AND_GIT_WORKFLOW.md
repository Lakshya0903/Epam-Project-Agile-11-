# FarmCart Phase 2 — Contributor Attribution, Commit Messages & Git Workflow Standard

This document establishes the official engineering standard for contributor attribution, Git trailers, commit messages, and repository workflow across the 11-member FarmCart engineering team.

---

## 1. Mandatory Sign-Off Rule

Every project commit must contain this exact sign-off line as its final trailer:

```text
Signed-off-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>
```

### Critical Distinctions:
1. **The actual contributor must remain the Git commit author:**
   - Commit author is set via `git commit --author="Contributor Name <email>"`.
2. **Lakshya Raj Malviya must always appear in the Signed-off-by trailer:**
   - Lakshya serves as the consistent sign-off authority and project lead for all commits.
3. **Do NOT change the actual Git author to Lakshya** merely to make the sign-off consistent.
4. **Do NOT falsely claim that Lakshya personally implemented every change.**
5. **Do NOT remove or rewrite legitimate contribution credits.**

---

## 2. Team Directory & Verified Email Addresses

Every contributor must use their exact verified email address for Git author attribution and trailers:

| Contributor | Verified Email Address | Designated Responsibility |
|---|---|---|
| **Mansi Jain** | `mansijain1618@gmail.com` | Data Analyst, Testing Engineer, metrics and data quality |
| **Raksha Pandey** | `raksha.pandeyyy@gmail.com` | Frontend Lead, database development, buyer-facing workflows |
| **Alankrit Purohit** | `purohitak21@gmail.com` | AI/ML Lead, optimization research and feasibility analysis |
| **Harshika Singh** | `harshikasingh212@gmail.com` | Research Lead, frontend development, dashboards and dispute interfaces |
| **Sneha Sanodiya** | `snehasanodia1@gmail.com` | Team Lead, QA Lead, coordination, acceptance criteria, release readiness |
| **Yash Goyal** | `yashgoyal09102005@gmail.com` | Backend Developer, serviceability, inventory and produce logic |
| **Aparna Jha** | `aparnajha2021@gmail.com` | Testing Engineer, Research Engineer, validation and quality assurance |
| **Anshika Sharma** | `anshika2907sharma@gmail.com` | Backend/deployment responsibilities, configuration and release infrastructure |
| **Swyam Shukla** | `swyamshukla0104@gmail.com` | Database Lead, API Integration Engineer, models, schemas and migrations |
| **Hemant Yadav** | `hemantyadav6090@gmail.com` | Backend Developer, logistics, delivery confirmation and payment integrations |
| **Lakshya Raj Malviya** | `177052558+Lakshya0903@users.noreply.github.com` | Backend Lead, AI/ML Engineer, architecture and integration oversight |

---

## 3. Git Attribution Trailers

For every commit, inspect the actual changes and determine who genuinely contributed:

### A. Co-authored-by
Use when another team member materially contributed to implementing the code, documentation, or design in that commit.
```text
Co-authored-by: Full Name <email>
```
*Note: Only credit genuine co-authors. Do not add the entire team to every commit.*

### B. Signed-off-by
Always include Lakshya's mandatory sign-off trailer:
```text
Signed-off-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>
```

### C. Reviewed-by
Use when a team member actually reviewed the changes, inspected implementation quality, or validated relevant test suites.
```text
Reviewed-by: Full Name <email>
```

### D. Researched-by
Use when a team member materially contributed research, technical investigation, feasibility analysis, or supporting technical documentation.
```text
Researched-by: Full Name <email>
```

---

## 4. Commit Message Structure

Follow the Conventional Commits structure consistently:

```text
<type>(<scope>): <short description>

<Detailed body explaining what was implemented, why the change was
necessary, important technical details, and validation performed.>

[Optional Co-authored-by: Full Name <email>]
[Optional Researched-by: Full Name <email>]
[Optional Reviewed-by: Full Name <email>]
Signed-off-by: Lakshya Raj Malviya <177052558+Lakshya0903@users.noreply.github.com>
```

---

## 5. Step-by-Step Contributor Workflow

### Step 1: Pull Latest Main
```bash
git checkout main
git pull origin main
```

### Step 2: Switch to Assigned Feature Branch
```bash
git checkout -b <your-assigned-feature-branch>
```

### Step 3: Review Assigned Deliverables Folder
Navigate to your assigned task directory inside `phase 2 deliveries/`:
- Read `TASK.md` for exact files, protected boundaries, and acceptance criteria.
- Inspect the source files in `files/`.

### Step 4: Apply Changes to Repository
Copy or apply files from `files/` preserving relative repository paths. Verify diff with `git diff`.

### Step 5: Execute Automated Verification Tests
```bash
python -m unittest discover tests
```
Ensure all 50 tests pass with 0 failures and 0 errors.

### Step 6: Create the Git Commit with Full Attribution
Stage only your assigned files:
```bash
git add <file1> <file2> ...
```
Commit using your verified email and the pre-formatted `COMMIT_MESSAGE.txt`:
```bash
git commit --author="Your Name <your.email@gmail.com>" -F COMMIT_MESSAGE.txt
```

### Step 7: Push and Open Pull Request
```bash
git push -u origin <your-assigned-feature-branch>
```
Open a PR against `main`. Follow the 6-wave integration order documented in `INTEGRATION_ORDER.md`.
