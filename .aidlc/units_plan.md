# Units Plan

## Objective

Group the 21 user stories from `.aidlc/user_stories.md` into independently buildable units, ordered by dependency. Each unit gets a spec folder under `specs/` with requirements, design, and tasks.

## Proposed Units (in build order)

1. **Unit 1 — Foundation & Auth** (US-1.1, US-1.2, US-1.3, US-1.4, US-2.1, US-2.2, US-2.3, US-2.4)
   - SAM template, S3 buckets, DDB tables, API Gateway, Lambda scaffold, React app shell
   - Admin seed account, login, logout, session validation
   - Rationale: Everything else depends on infrastructure + auth being in place

2. **Unit 2 — User & Folder Management** (US-3.1, US-3.2, US-3.3, US-3.4, US-4.1, US-4.2, US-4.3, US-4.4)
   - Admin CRUD for users (with role + folder assignment) and folders
   - Rationale: Users and folders are tightly coupled (assigning folders to users), and both must exist before files can be uploaded. Grouped together since admin manages both and the Lambda can be consolidated.

3. **Unit 3 — File Operations & RBAC** (US-5.1, US-5.2, US-5.3, US-7.1, US-7.2, US-7.3, US-7.4)
   - Upload, download, view file metadata — all gated by role-based access control
   - Rationale: File operations and RBAC enforcement are inseparable — every file action checks the user's role and folder assignment. Building them together avoids building file ops without access control.

4. **Unit 4 — Browsing, Search & Sort** (US-6.1, US-6.2)
   - Search by name, sort by name/date/size
   - Rationale: This is a front-end enhancement on top of the file listing from Unit 3. Loosely coupled — can be built after file viewing works.

## Deliverables (per unit)

- `specs/unit-N/requirements.md` — User stories included, with acceptance criteria
- `specs/unit-N/design.md` — Architecture, DDB schema, API contracts, component design
- `specs/unit-N/tasks.md` — Ordered implementation tasks with checkboxes

## Plan

- [x] **Step 1: Create `specs/unit-1/` — Foundation & Auth**
  - Write requirements.md, design.md, tasks.md
  - ✅ Resolved: Hardcoded admin password with forced change on first login

- [x] **Step 2: Create `specs/unit-2/` — User & Folder Management**
  - Write requirements.md, design.md, tasks.md
  - ✅ Resolved: Single-table DDB design

- [x] **Step 3: Create `specs/unit-3/` — File Operations & RBAC**
  - Write requirements.md, design.md, tasks.md

- [x] **Step 4: Create `specs/unit-4/` — Browsing, Search & Sort**
  - Write requirements.md, design.md, tasks.md

- [x] **Step 5: Final cross-check**
  - Verified all 21 user stories are covered across the 4 units
  - Verified unit ordering respects all dependencies: Unit 1 → Unit 2 → Unit 3 → Unit 4
