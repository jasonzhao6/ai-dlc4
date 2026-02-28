# Unit 1: Foundation & Auth — Requirements

## Overview

Stand up all infrastructure (S3, DynamoDB, API Gateway, Lambda, React shell) and implement authentication with session management. This unit is the foundation for all subsequent units.

## User Stories Included

### US-1.1: Provision S3 Buckets

**As a** developer,
**I want** S3 buckets provisioned for file storage and React static site hosting,
**So that** the system has its core storage layer ready.

**Acceptance Criteria:**
- A file storage S3 bucket is created with versioning disabled
- A separate S3 bucket is created and configured for static website hosting (React front-end)
- Bucket policies restrict public access appropriately (file bucket is private, static site bucket allows public read)

---

### US-1.2: Provision DynamoDB Table

**As a** developer,
**I want** a single DynamoDB table created using single-table design for users, sessions, and folder structure,
**So that** the application has its database layer ready.

**Acceptance Criteria:**
- A single DynamoDB table is created using single-table design
- Partition key and sort key support entities: users, sessions, folders, folder-assignments, and file metadata
- A GSI is available for session token lookups
- Sessions use DynamoDB TTL for automatic expiration
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

### US-2.1: Admin Seed Account

**As a** system,
**I want** a single admin account created as part of the initial build,
**So that** there is a bootstrapped admin who can manage the system from day one.

**Acceptance Criteria:**
- An admin user record is seeded into the DynamoDB table during initial deployment
- The admin has a hardcoded default password
- On first login, the admin is forced to change the default password
- The admin has full access to all system functionality

---

### US-2.2: User Login

**As a** user (any role),
**I want** to log in with my credentials,
**So that** I can access the system according to my role.

**Acceptance Criteria:**
- A login endpoint (`POST /auth/login`) accepts username and password
- On success, a session is created in DynamoDB and a session token is returned
- On failure, an appropriate error message is returned
- Session has a defined TTL for expiration

---

### US-2.3: User Logout

**As a** user (any role),
**I want** to log out of the system,
**So that** my session is terminated and access is revoked.

**Acceptance Criteria:**
- A logout endpoint (`POST /auth/logout`) deletes the session record from DynamoDB
- After logout, the session token is no longer valid for any API call

---

### US-2.4: Session Validation

**As the** system,
**I want** to validate the session token on every API request,
**So that** only authenticated users can access protected resources.

**Acceptance Criteria:**
- Every protected API endpoint checks for a valid session token via the `Authorization` header
- Expired or missing tokens return a 401 Unauthorized response
