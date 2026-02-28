# Unit 3: File Operations & RBAC — Requirements

## Overview

File upload, download, and viewing — all gated by role-based access control. Depends on Unit 1 (auth) and Unit 2 (users, folders, assignments).

## User Stories Included

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
