# User Stories — S3 File-Sharing System

---

## Epic 1: Infrastructure Setup

### US-1.1: Provision S3 Buckets

**As a** developer,
**I want** S3 buckets provisioned for file storage and React static site hosting,
**So that** the system has its core storage layer ready.

**Acceptance Criteria:**
- A file storage S3 bucket is created with versioning disabled
- A separate S3 bucket is created and configured for static website hosting (React front-end)
- Bucket policies restrict public access appropriately (file bucket is private, static site bucket allows public read)

---

### US-1.2: Provision DynamoDB Tables

**As a** developer,
**I want** DynamoDB tables created for users, sessions, and folder structure,
**So that** the application has its database layer ready.

**Acceptance Criteria:**
- A users table is created to store user accounts and role assignments
- A sessions table is created for session management with TTL enabled
- A folders table is created to store folder metadata and user-folder assignments
- The Decimal type from DynamoDB is handled properly (not JSON serializable) in all Lambda code

---

### US-1.3: Provision API Gateway and Lambda Functions

**As a** developer,
**I want** an API Gateway and Python Lambda functions deployed via AWS SAM,
**So that** the back-end is operational and accessible from the front-end.

**Acceptance Criteria:**
- API Gateway is created with RESTful endpoints for all back-end operations
- Lambda functions are written in Python using the locally installed Python version (no containers)
- CRUD operations are consolidated into one Lambda function per resource where applicable
- SAM template defines all resources
- Every API Gateway method has a corresponding HTTPS integration test confirming correct response

---

### US-1.4: Deploy React Front-End

**As a** developer,
**I want** a React JS static site built and deployed to S3,
**So that** users can access the file-sharing system through a web browser.

**Acceptance Criteria:**
- React app is built and uploaded to the static site S3 bucket
- The app loads in a browser and can communicate with the API Gateway back-end

---

## Epic 2: Authentication & Session Management

### US-2.1: Admin Seed Account

**As a** system,
**I want** a single admin account created as part of the initial build,
**So that** there is a bootstrapped admin who can manage the system from day one.

**Acceptance Criteria:**
- An admin user record is seeded into the DynamoDB users table during initial deployment
- The admin has full access to all system functionality

---

### US-2.2: User Login

**As a** user (any role),
**I want** to log in with my credentials,
**So that** I can access the system according to my role.

**Acceptance Criteria:**
- A login endpoint accepts username and password
- On success, a session is created in DynamoDB and a session token is returned
- On failure, an appropriate error message is returned
- Session has a defined TTL for expiration

---

### US-2.3: User Logout

**As a** user (any role),
**I want** to log out of the system,
**So that** my session is terminated and access is revoked.

**Acceptance Criteria:**
- A logout endpoint deletes the session record from DynamoDB
- After logout, the session token is no longer valid for any API call

---

### US-2.4: Session Validation

**As the** system,
**I want** to validate the session token on every API request,
**So that** only authenticated users can access protected resources.

**Acceptance Criteria:**
- Every protected API endpoint checks for a valid session token
- Expired or missing tokens return a 401 Unauthorized response

---

## Epic 3: User Management

### US-3.1: Create User

**As an** admin,
**I want** to create new user accounts with a specified role and folder assignments,
**So that** I can onboard people to the file-sharing system.

**Acceptance Criteria:**
- Admin can create a user with a username, password, and role (admin, uploader, reader, or viewer)
- Admin can assign one or more folders to the user at creation time
- The new user record is stored in DynamoDB
- Non-admin users cannot access this functionality

---

### US-3.2: Update User

**As an** admin,
**I want** to update an existing user's role or folder assignments,
**So that** I can adjust access as needs change.

**Acceptance Criteria:**
- Admin can change a user's role
- Admin can add or remove folder assignments for a user
- Changes take effect on the user's next API request
- Non-admin users cannot access this functionality

---

### US-3.3: Delete User

**As an** admin,
**I want** to delete a user account,
**So that** former users no longer have access to the system.

**Acceptance Criteria:**
- Admin can delete a user by username
- The user's record is removed from DynamoDB
- Any active sessions for the deleted user are invalidated
- Non-admin users cannot access this functionality

---

### US-3.4: List Users

**As an** admin,
**I want** to view a list of all users and their roles,
**So that** I can manage the user base.

**Acceptance Criteria:**
- Admin can retrieve a list of all users with their roles and folder assignments
- Non-admin users cannot access this functionality

---

## Epic 4: Folder Management

### US-4.1: Create Folder

**As an** admin,
**I want** to create folders in the system,
**So that** files can be organized and access can be controlled per folder.

**Acceptance Criteria:**
- Admin can create a named folder
- Folder metadata is stored in DynamoDB
- The corresponding S3 prefix/path is established
- Non-admin users cannot access this functionality

---

### US-4.2: Rename Folder

**As an** admin,
**I want** to rename an existing folder,
**So that** I can correct or update folder names as needed.

**Acceptance Criteria:**
- Admin can rename a folder
- All user-folder assignments are updated to reflect the new name
- S3 objects under the old prefix are moved to the new prefix
- Non-admin users cannot access this functionality

---

### US-4.3: Delete Folder

**As an** admin,
**I want** to delete a folder,
**So that** I can remove folders that are no longer needed.

**Acceptance Criteria:**
- Admin can delete a folder by name
- All objects within the folder in S3 are deleted
- All user-folder assignments referencing the folder are removed
- Non-admin users cannot access this functionality

---

### US-4.4: List Folders

**As an** admin,
**I want** to view all folders in the system,
**So that** I can manage folder structure and assignments.

**Acceptance Criteria:**
- Admin can retrieve a list of all folders
- Non-admin users only see folders they are assigned to

---

## Epic 5: File Operations

### US-5.1: Upload File

**As an** uploader (or admin),
**I want** to upload a file to a folder I have access to,
**So that** I can share files with others.

**Acceptance Criteria:**
- User requests a pre-signed S3 URL for upload
- The upload is performed directly to S3 via the pre-signed URL (not through API Gateway/Lambda)
- Maximum file size is 1GB
- File metadata (name, size, upload date, uploader) is recorded in DynamoDB
- Reader and viewer personas cannot upload
- Users can only upload to folders they are assigned to

---

### US-5.2: Download File

**As a** reader (or uploader or admin),
**I want** to download a file from a folder I have access to,
**So that** I can retrieve shared files.

**Acceptance Criteria:**
- User requests a pre-signed S3 URL for download
- The download is performed directly from S3 via the pre-signed URL
- Viewer persona cannot download
- Users can only download from folders they are assigned to

---

### US-5.3: View File Metadata

**As a** viewer (or reader, uploader, or admin),
**I want** to view file details (name, size, upload date) in folders I have access to,
**So that** I can see what files are available.

**Acceptance Criteria:**
- User can see a list of files in their assigned folders
- Each file displays: name, size, and date uploaded
- Users only see files in folders they are assigned to

---

## Epic 6: Browsing, Search & Sort

### US-6.1: Search Files by Name

**As a** user (any role),
**I want** to search for files by name within my assigned folders,
**So that** I can quickly find specific files.

**Acceptance Criteria:**
- A search input filters the file list by partial or full file name match
- Search is scoped to the user's assigned folders only

---

### US-6.2: Sort Files

**As a** user (any role),
**I want** to sort the file list by name, date uploaded, or file size,
**So that** I can organize my view of files.

**Acceptance Criteria:**
- User can sort by file name (alphabetical, ascending/descending)
- User can sort by date uploaded (ascending/descending)
- User can sort by file size (ascending/descending)
- Default sort order is defined (e.g., alphabetical by name ascending)

---

## Epic 7: Role-Based Access Control

### US-7.1: Enforce Admin Permissions

**As the** system,
**I want** to grant admin users full access to all features,
**So that** admins can manage users, folders, and files without restriction.

**Acceptance Criteria:**
- Admin can access all API endpoints
- Admin can view all folders and files regardless of assignment

---

### US-7.2: Enforce Uploader Permissions

**As the** system,
**I want** to restrict uploaders to viewing, uploading, and downloading in their assigned folders only,
**So that** uploaders cannot exceed their intended access.

**Acceptance Criteria:**
- Uploader can view files in assigned folders
- Uploader can upload files to assigned folders
- Uploader can download files from assigned folders
- Uploader cannot access user management or folder management
- Uploader cannot access unassigned folders

---

### US-7.3: Enforce Reader Permissions

**As the** system,
**I want** to restrict readers to viewing and downloading in their assigned folders only,
**So that** readers cannot upload or access unassigned content.

**Acceptance Criteria:**
- Reader can view files in assigned folders
- Reader can download files from assigned folders
- Reader cannot upload files
- Reader cannot access user management or folder management
- Reader cannot access unassigned folders

---

### US-7.4: Enforce Viewer Permissions

**As the** system,
**I want** to restrict viewers to only viewing file metadata in their assigned folders,
**So that** viewers cannot download, upload, or access unassigned content.

**Acceptance Criteria:**
- Viewer can view file metadata (name, size, date) in assigned folders
- Viewer cannot download files
- Viewer cannot upload files
- Viewer cannot access user management or folder management
- Viewer cannot access unassigned folders
