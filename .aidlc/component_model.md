# Component Model — S3 File-Sharing System

---

## 1. Component Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React SPA)                        │
│                                                                     │
│  LoginPage ─── DashboardPage ─── UserMgmtPage ─── FolderMgmtPage  │
│                      │                                              │
│               FolderDetailPage                                      │
│               ┌─────┴──────┐                                        │
│           SearchBar   SortableFileTable                             │
│                                                                     │
│  ──────────────── ApiClient ────────────────                        │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────┴──────────────────────────────────────────────┐
│                      API Gateway                                    │
└──┬───────────┬───────────────┬──────────────────┬───────────────────┘
   │           │               │                  │
┌──┴──┐   ┌───┴────┐   ┌──────┴───┐   ┌──────────┴──┐
│Auth │   │User    │   │Folder    │   │File         │
│Svc  │   │Manager │   │Manager   │   │Manager      │
└──┬──┘   └───┬────┘   └──────┬───┘   └──────┬──────┘
   │          │               │               │
   │    ┌─────┴───────────────┴───────────────┴──────┐
   │    │           AccessControl                     │
   │    └─────────────────┬──────────────────────────-┘
   │                      │
   ├──────────┬───────────┤
   │          │           │
┌──┴──┐  ┌───┴────┐  ┌───┴────┐
│Sess.│  │Data    │  │File    │
│Valid.│  │Store   │  │Store   │
└─────┘  └────────┘  └────────┘
```

---

## 2. Backend Components

---

### 2.1 AuthService

Handles user authentication lifecycle.

**Attributes:**
- defaultAdminUsername: the hardcoded admin username for seeding
- defaultAdminPasswordHash: the hardcoded admin password hash for seeding
- sessionTtlSeconds: TTL duration for sessions

**Behaviors:**
- login(username, password) → sessionToken
  - Retrieves user from DataStore, verifies password hash, creates session via DataStore, returns token and force_password_change flag
- logout(sessionToken)
  - Deletes session from DataStore
- changePassword(sessionToken, oldPassword, newPassword)
  - Validates old password, updates password hash in DataStore, clears force_password_change flag
- seedAdminAccount()
  - Creates the default admin user in DataStore with force_password_change=true

**Depends on:** DataStore, SessionValidator

**User stories:** US-2.1, US-2.2, US-2.3

---

### 2.2 SessionValidator

Validates session tokens on every protected API request. Shared by all other backend components.

**Attributes:**
- (none — stateless utility)

**Behaviors:**
- validate(sessionToken) → { username, role } or 401 error
  - Looks up session in DataStore, checks TTL, returns user identity and role

**Depends on:** DataStore

**User stories:** US-2.4

---

### 2.3 AccessControl

Centralized authorization logic. Determines whether a user can perform a given action on a given resource.

**Attributes:**
- permissionMatrix: maps (role, action) → allowed/denied
  - admin: all actions, all folders
  - uploader: view, upload, download — assigned folders only
  - reader: view, download — assigned folders only
  - viewer: view — assigned folders only

**Behaviors:**
- checkAdmin(role) → allowed or 403
  - Returns true if role is admin, otherwise 403
- checkFolderAccess(username, role, folderName) → allowed or 403
  - Admin: always allowed. Others: queries DataStore for folder assignment
- checkFileAction(role, action) → allowed or 403
  - Evaluates the permission matrix for the given role and action (view/upload/download)
- authorize(username, role, folderName, action) → allowed or 403
  - Combines checkFolderAccess + checkFileAction in one call

**Depends on:** DataStore

**User stories:** US-7.1, US-7.2, US-7.3, US-7.4

---

### 2.4 UserManager

Admin-only CRUD operations for user accounts and folder assignments.

**Attributes:**
- (none — stateless, operates on DataStore)

**Behaviors:**
- createUser(username, password, role, folderNames[])
  - Stores user record and folder assignment records in DataStore
- updateUser(username, { role?, folderNames[]? })
  - Updates user role and/or diffs folder assignments (add new, remove old) in DataStore
- deleteUser(username)
  - Removes user record, all folder assignments, and all active sessions from DataStore
- listUsers() → [{ username, role, folderNames[] }]
  - Retrieves all users and their folder assignments from DataStore

**Depends on:** SessionValidator, AccessControl, DataStore

**User stories:** US-3.1, US-3.2, US-3.3, US-3.4

---

### 2.5 FolderManager

Admin-only CRUD operations for folders. List is available to all authenticated users (filtered by assignment).

**Attributes:**
- (none — stateless, operates on DataStore and FileStore)

**Behaviors:**
- createFolder(folderName)
  - Creates folder record in DataStore, establishes S3 prefix in FileStore
- renameFolder(oldName, newName)
  - Creates new folder record, migrates all folder assignments, file metadata records in DataStore, and S3 objects in FileStore from old prefix to new prefix, then deletes old records
- deleteFolder(folderName)
  - Deletes all S3 objects in FileStore, all file metadata, all folder assignments, and the folder record from DataStore
- listFolders(username, role) → [{ folderName, createdAt }]
  - Admin: returns all folders. Others: returns only assigned folders via DataStore

**Depends on:** SessionValidator, AccessControl, DataStore, FileStore

**User stories:** US-4.1, US-4.2, US-4.3, US-4.4

---

### 2.6 FileManager

File upload, download, and metadata viewing — gated by RBAC.

**Attributes:**
- maxFileSizeBytes: 1,073,741,824 (1GB)
- presignedUrlExpirySeconds: 900 (15 min)

**Behaviors:**
- listFiles(folderName) → [{ fileName, size, uploadedBy, uploadedAt }]
  - Queries DataStore for file metadata in the folder
- requestUploadUrl(folderName, fileName, fileSize) → { uploadUrl, s3Key }
  - Validates fileSize ≤ maxFileSizeBytes, generates pre-signed PUT URL from FileStore
- completeUpload(folderName, fileName, fileSize, uploadedBy)
  - Records file metadata in DataStore
- requestDownloadUrl(folderName, fileName) → { downloadUrl }
  - Generates pre-signed GET URL from FileStore

**Depends on:** SessionValidator, AccessControl, DataStore, FileStore

**User stories:** US-5.1, US-5.2, US-5.3

---

### 2.7 DataStore

Abstraction over the DynamoDB single table. All other backend components go through DataStore for persistence.

**Attributes:**
- tableName: "FileShareTable"
- partitionKey: "PK"
- sortKey: "SK"
- gsi1PartitionKey: "GSI1PK"
- gsi1SortKey: "GSI1SK"

**Behaviors:**
- putItem(item)
- getItem(pk, sk) → item
- queryByPk(pk, skPrefix?) → [items]
- queryGsi1(gsi1pk, gsi1skPrefix?) → [items]
- deleteItem(pk, sk)
- scanByPkPrefix(pkPrefix, skPrefix?) → [items]
- batchWrite(putItems[], deleteKeys[])

**Depends on:** DynamoDB (AWS)

**User stories:** US-1.2 (provisioned via SAM, used by all components)

---

### 2.8 FileStore

Abstraction over S3 file bucket. Used by FileManager and FolderManager.

**Attributes:**
- bucketName: "fileshare-files-{account-id}"

**Behaviors:**
- generatePresignedPutUrl(s3Key, expirySeconds) → url
- generatePresignedGetUrl(s3Key, expirySeconds) → url
- copyObject(sourceKey, destKey)
- deleteObject(s3Key)
- deleteByPrefix(prefix)
- listObjectsByPrefix(prefix) → [s3Keys]

**Depends on:** S3 (AWS)

**User stories:** US-1.1 (provisioned via SAM, used by FileManager and FolderManager)

---

## 3. Frontend Components

---

### 3.1 ApiClient

Centralized HTTP client for all API calls. Injects session token into every request.

**Attributes:**
- baseUrl: API Gateway URL
- sessionToken: current auth token (stored in sessionStorage)

**Behaviors:**
- post(path, body) → response
- get(path) → response
- put(path, body) → response
- delete(path) → response
- setToken(token) / clearToken()
- All methods attach `Authorization: {sessionToken}` header

**Depends on:** API Gateway (network)

**User stories:** Supports all frontend stories

---

### 3.2 LoginPage

Login form and forced password change flow.

**Attributes:**
- usernameInput, passwordInput
- newPasswordInput (for forced change)
- errorMessage
- forcePasswordChange: boolean flag from login response

**Behaviors:**
- submitLogin() → calls ApiClient.post("/auth/login"), stores token, checks force_password_change flag
- submitPasswordChange() → calls ApiClient.post("/auth/change-password"), then redirects to dashboard
- redirectToDashboard()

**Depends on:** ApiClient

**User stories:** US-2.1, US-2.2

---

### 3.3 DashboardPage

Landing page after login. Routes to role-appropriate views.

**Attributes:**
- currentUser: { username, role }
- assignedFolders: list of folder objects

**Behaviors:**
- loadFolders() → calls ApiClient.get("/folders"), populates assignedFolders
- navigateToFolder(folderName) → opens FolderDetailPage
- showAdminNav() → shows links to UserManagementPage and FolderManagementPage (admin only)
- logout() → calls ApiClient.post("/auth/logout"), clears token, redirects to LoginPage

**Depends on:** ApiClient, FolderDetailPage, UserManagementPage, FolderManagementPage

**User stories:** US-2.3, US-4.4

---

### 3.4 UserManagementPage

Admin-only page for managing users.

**Attributes:**
- userList: [{ username, role, folderNames[] }]
- userForm: { username, password, role, selectedFolders[] }
- availableFolders: list of all folders (for multi-select)

**Behaviors:**
- loadUsers() → calls ApiClient.get("/users")
- createUser() → calls ApiClient.post("/users", userForm)
- updateUser(username) → calls ApiClient.put("/users/{username}", changes)
- deleteUser(username) → calls ApiClient.delete("/users/{username}")

**Depends on:** ApiClient

**User stories:** US-3.1, US-3.2, US-3.3, US-3.4

---

### 3.5 FolderManagementPage

Admin-only page for managing folders.

**Attributes:**
- folderList: [{ folderName, createdAt }]
- folderForm: { folderName }

**Behaviors:**
- loadFolders() → calls ApiClient.get("/folders")
- createFolder() → calls ApiClient.post("/folders", folderForm)
- renameFolder(oldName, newName) → calls ApiClient.put("/folders/{oldName}", { newName })
- deleteFolder(folderName) → calls ApiClient.delete("/folders/{folderName}")

**Depends on:** ApiClient

**User stories:** US-4.1, US-4.2, US-4.3, US-4.4

---

### 3.6 FolderDetailPage

Displays files in a folder. Hosts SearchBar and SortableFileTable.

**Attributes:**
- folderName: current folder
- files: [{ fileName, size, uploadedBy, uploadedAt }] (full list from API)
- filteredFiles: files after search filter applied
- searchTerm: current search string
- currentUserRole: determines which actions are visible

**Behaviors:**
- loadFiles() → calls ApiClient.get("/folders/{folderName}/files")
- onSearchChange(term) → filters files by name, updates filteredFiles
- requestUpload(fileName, fileSize) → calls ApiClient.post(".../upload"), uploads to S3 via pre-signed URL, then calls ".../upload/complete"
- requestDownload(fileName) → calls ApiClient.post(".../download"), triggers browser download via pre-signed URL

**Depends on:** ApiClient, SearchBar, SortableFileTable

**User stories:** US-5.1, US-5.2, US-5.3, US-6.1

---

### 3.7 SearchBar

Reusable search input for filtering file lists.

**Attributes:**
- searchTerm: current input value

**Behaviors:**
- onChange(term) → emits filter string to parent component
- clear() → resets searchTerm, emits empty string

**Depends on:** (none — presentational, communicates via callbacks)

**User stories:** US-6.1

---

### 3.8 SortableFileTable

Displays file list with sortable column headers.

**Attributes:**
- files: the filtered file list from parent
- sortColumn: "name" | "uploadedAt" | "size"
- sortDirection: "asc" | "desc"

**Behaviors:**
- toggleSort(column) → if same column, flip direction; if new column, set ascending
- sortFiles() → sorts files in memory by sortColumn + sortDirection
- renderRow(file) → displays file name, size, upload date, and action buttons (upload/download) based on role

**Depends on:** (none — presentational, receives data and role via props)

**User stories:** US-6.2

---

## 4. Component Interactions by Flow

---

### 4.1 Login Flow (US-2.1, US-2.2)

```
LoginPage → ApiClient → API Gateway → AuthService → DataStore
                                                        │
                                          (verify password hash,
                                           create session record)
                                                        │
                                       ← sessionToken + forcePasswordChange flag
```

If forcePasswordChange is true:
```
LoginPage (change password form) → ApiClient → API Gateway → AuthService → DataStore
                                                                              │
                                                               (update password hash,
                                                                clear flag)
```

---

### 4.2 Admin Creates User with Folder Assignments (US-3.1)

```
UserManagementPage → ApiClient → API Gateway → SessionValidator → DataStore
                                                     │
                                               (validate token)
                                                     │
                                               AccessControl
                                                     │
                                               (checkAdmin)
                                                     │
                                               UserManager → DataStore
                                                                │
                                                  (put user record +
                                                   folder assignment records)
```

---

### 4.3 File Upload Flow (US-5.1, US-7.2)

```
FolderDetailPage → ApiClient → API Gateway → SessionValidator → DataStore
                                                    │
                                              AccessControl
                                                    │
                                        (checkFolderAccess + checkFileAction "upload")
                                                    │
                                              FileManager → FileStore
                                                               │
                                                  (generatePresignedPutUrl)
                                                               │
                                          ← { uploadUrl, s3Key }

FolderDetailPage → (direct S3 upload via pre-signed URL) → S3

FolderDetailPage → ApiClient → API Gateway → FileManager → DataStore
                                                               │
                                                  (put file metadata record)
```

---

### 4.4 File Download Flow (US-5.2, US-7.3)

```
FolderDetailPage → ApiClient → API Gateway → SessionValidator → DataStore
                                                    │
                                              AccessControl
                                                    │
                                        (checkFolderAccess + checkFileAction "download")
                                                    │
                                              FileManager → FileStore
                                                               │
                                                  (generatePresignedGetUrl)
                                                               │
                                          ← { downloadUrl }

FolderDetailPage → (direct S3 download via pre-signed URL) → S3
```

---

### 4.5 Browse Files with Search & Sort (US-5.3, US-6.1, US-6.2)

```
FolderDetailPage → ApiClient → API Gateway → SessionValidator → DataStore
                                                    │
                                              AccessControl
                                                    │
                                        (checkFolderAccess + checkFileAction "view")
                                                    │
                                              FileManager → DataStore
                                                               │
                                                  (query file metadata)
                                                               │
                                          ← [{ fileName, size, uploadedBy, uploadedAt }]

FolderDetailPage:
  files ← API response
  searchTerm ← SearchBar.onChange()
  filteredFiles ← files.filter(name contains searchTerm)
  SortableFileTable ← receives filteredFiles, applies sort
```

---

### 4.6 Folder Rename Flow (US-4.2)

```
FolderManagementPage → ApiClient → API Gateway → SessionValidator → DataStore
                                                        │
                                                  AccessControl (checkAdmin)
                                                        │
                                                  FolderManager
                                                     │     │
                                               DataStore   FileStore
                                                  │           │
                                    (migrate folder record,   (copy objects to
                                     assignments, file         new prefix,
                                     metadata to new name)     delete old)
```

---

## 5. User Story to Component Mapping

- US-1.1 → FileStore (provisioned via SAM)
- US-1.2 → DataStore (provisioned via SAM)
- US-1.3 → All backend components (deployed via SAM)
- US-1.4 → All frontend components (deployed to S3)
- US-2.1 → AuthService.seedAdminAccount, LoginPage
- US-2.2 → AuthService.login, LoginPage
- US-2.3 → AuthService.logout, DashboardPage
- US-2.4 → SessionValidator.validate
- US-3.1 → UserManager.createUser, UserManagementPage
- US-3.2 → UserManager.updateUser, UserManagementPage
- US-3.3 → UserManager.deleteUser, UserManagementPage
- US-3.4 → UserManager.listUsers, UserManagementPage
- US-4.1 → FolderManager.createFolder, FolderManagementPage
- US-4.2 → FolderManager.renameFolder, FolderManagementPage
- US-4.3 → FolderManager.deleteFolder, FolderManagementPage
- US-4.4 → FolderManager.listFolders, DashboardPage, FolderManagementPage
- US-5.1 → FileManager.requestUploadUrl + completeUpload, AccessControl.authorize, FolderDetailPage
- US-5.2 → FileManager.requestDownloadUrl, AccessControl.authorize, FolderDetailPage
- US-5.3 → FileManager.listFiles, AccessControl.authorize, FolderDetailPage
- US-6.1 → SearchBar, FolderDetailPage.onSearchChange
- US-6.2 → SortableFileTable.toggleSort + sortFiles
- US-7.1 → AccessControl.checkAdmin + permissionMatrix (admin row)
- US-7.2 → AccessControl.authorize + permissionMatrix (uploader row)
- US-7.3 → AccessControl.authorize + permissionMatrix (reader row)
- US-7.4 → AccessControl.authorize + permissionMatrix (viewer row)
