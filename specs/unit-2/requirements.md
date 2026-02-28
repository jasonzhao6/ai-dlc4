# Unit 2: User & Folder Management — Requirements

## Overview

Admin CRUD operations for users and folders. Depends on Unit 1 (infrastructure, auth, session validation).

## User Stories Included

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
- All folder assignment records for the user are removed
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
- All file metadata records are updated to reflect the new folder name
- S3 objects under the old prefix are copied to the new prefix and old objects deleted
- Non-admin users cannot access this functionality

---

### US-4.3: Delete Folder

**As an** admin,
**I want** to delete a folder,
**So that** I can remove folders that are no longer needed.

**Acceptance Criteria:**
- Admin can delete a folder by name
- All objects within the folder in S3 are deleted
- All file metadata records for the folder are removed from DynamoDB
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
