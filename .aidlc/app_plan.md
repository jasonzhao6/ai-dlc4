# Application Build Plan

## Environment

- Python: 3.12.11
- Node: 25.6.1
- SAM CLI: 1.154.0
- AWS credentials: NOT configured (need to resolve before deploy)

## Deliverables

- `template.yaml` — SAM template (DDB, S3 buckets, API Gateway, Lambdas, IAM)
- `backend/shared/` — Shared Python layer (DataStore, FileStore, SessionValidator, AccessControl, JSON encoder)
- `backend/auth/` — Auth Lambda (login, logout, change-password, seed)
- `backend/users/` — Users Lambda (CRUD)
- `backend/folders/` — Folders Lambda (CRUD)
- `backend/files/` — Files Lambda (upload, download, list)
- `backend/seed/` — Admin seed custom resource Lambda
- `frontend/` — React app (LoginPage, Dashboard, UserMgmt, FolderMgmt, FolderDetail, SearchBar, SortableFileTable)
- `scripts/verify_layer.sh` — Lambda layer structure verification script
- `TODO.md` — Post-deployment tasks tracker

## Plan

### Phase 1: Project Scaffolding & Infrastructure (Unit 1, Tasks 1–5)

- [x] **Step 1:** Create project directory structure, TODO.md, and SAM template skeleton with DDB table (PK, SK, GSI1, TTL), S3 file bucket, S3 frontend bucket, API Gateway with CORS
- [x] **Step 2:** Create Lambda shared layer — DataStore, FileStore, Decimal-safe JSON encoder, SessionValidator, AccessControl modules. Create `scripts/verify_layer.sh` to validate layer structure.
  - ✅ Resolved: Building locally, deploy steps in TODO.md

### Phase 2: Auth Lambda (Unit 1, Tasks 6–12)

- [x] **Step 3:** Create `auth_handler` Lambda — login, logout, change-password route dispatch
- [x] **Step 4:** Create admin seed Lambda (SAM custom resource) to insert default admin on deploy
- [x] **Step 5:** Test auth Lambda locally with `sam local invoke` and `sam local start-api`

### Phase 3: React Front-End Shell (Unit 1, Tasks 13–17)

- [x] **Step 6:** Initialize React app, install Bootstrap, set up teal/dark color theme, create ApiClient utility
- [x] **Step 7:** Build LoginPage (login form + forced password change form) and DashboardPage shell with logout
- [x] **Step 8:** Run `npm run build` to produce static assets

### Phase 4: Unit 1 Deploy & Integration Tests (Unit 1, Tasks 18–25)

- [x] **Step 9:** Add deploy commands and integration test scripts to TODO.md. If AWS credentials are available, deploy and run HTTPS tests for auth endpoints.

### Phase 5: Users Lambda (Unit 2, Tasks 1–7)

- [x] **Step 10:** Create `users_handler` Lambda — POST, GET, PUT, DELETE with admin auth check
- [x] **Step 11:** Add users Lambda + API Gateway routes to SAM template, test locally with `sam local`

### Phase 6: Folders Lambda (Unit 2, Tasks 8–14)

- [x] **Step 12:** Create `folders_handler` Lambda — POST, GET, PUT, DELETE with admin auth check, S3 operations for rename/delete
- [x] **Step 13:** Add folders Lambda + API Gateway routes to SAM template, test locally with `sam local`

### Phase 7: React — User & Folder Management (Unit 2, Tasks 15–17)

- [x] **Step 14:** Build UserManagementPage (list, create, update, delete users with role + folder assignment)
- [x] **Step 15:** Build FolderManagementPage (list, create, rename, delete folders)
- [x] **Step 16:** Build folder list view on DashboardPage for non-admin users, `npm run build`

### Phase 8: Unit 2 Deploy & Integration Tests (Unit 2, Tasks 18–29)

- [x] **Step 17:** Deploy and run HTTPS integration tests for users and folders endpoints (or add to TODO.md)

### Phase 9: Files Lambda (Unit 3, Tasks 1–7)

- [x] **Step 18:** Create `files_handler` Lambda — list files, upload (pre-signed URL + complete), download (pre-signed URL), with RBAC enforcement
- [x] **Step 19:** Add files Lambda + API Gateway routes to SAM template, test locally with `sam local`

### Phase 10: React — File Operations (Unit 3, Tasks 8–12)

- [x] **Step 20:** Build FolderDetailPage with file list, upload flow (pre-signed URL → S3 → complete), download flow, role-based button visibility
- [x] **Step 21:** `npm run build`

### Phase 11: Unit 3 Deploy & Integration Tests (Unit 3, Tasks 13–24)

- [x] **Step 22:** Deploy and run HTTPS integration tests for file operations + RBAC (or add to TODO.md)

### Phase 12: Search & Sort (Unit 4, Tasks 1–5)

- [x] **Step 23:** Add SearchBar and SortableFileTable components to FolderDetailPage, `npm run build`

### Phase 13: Final Deploy & Verification (Unit 4, Tasks 6–8)

- [x] **Step 24:** Final deploy, end-to-end verification, update TODO.md with any remaining items
