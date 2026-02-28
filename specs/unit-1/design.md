# Unit 1: Foundation & Auth — Design

## Architecture Overview

```
[React SPA in S3] --> [API Gateway] --> [Lambda Functions] --> [DynamoDB Single Table]
                                                           --> [S3 File Bucket]
```

## DynamoDB Single-Table Design

Single table name: `FileShareTable`

- Partition Key: `PK` (String)
- Sort Key: `SK` (String)
- GSI1: `GSI1PK` / `GSI1SK` for reverse lookups

### Entity Access Patterns

**User entity**
- PK: `USER#<username>`
- SK: `USER#<username>`
- Attributes: `username`, `password_hash`, `role`, `force_password_change`, `created_at`

**Session entity**
- PK: `SESSION#<token>`
- SK: `SESSION#<token>`
- Attributes: `username`, `role`, `created_at`, `ttl` (DDB TTL attribute)

**Folder entity**
- PK: `FOLDER#<folder_name>`
- SK: `FOLDER#<folder_name>`
- Attributes: `folder_name`, `s3_prefix`, `created_at`

**Folder Assignment entity** (which user has access to which folder)
- PK: `USER#<username>`
- SK: `FOLDER#<folder_name>`
- Attributes: `username`, `folder_name`, `assigned_at`
- GSI1PK: `FOLDER#<folder_name>`, GSI1SK: `USER#<username>` (reverse lookup: all users for a folder)

**File Metadata entity**
- PK: `FOLDER#<folder_name>`
- SK: `FILE#<file_name>`
- Attributes: `file_name`, `folder_name`, `s3_key`, `size`, `uploaded_by`, `uploaded_at`

### Key Access Patterns

- Get user: `PK = USER#<username>, SK = USER#<username>`
- Get session: `PK = SESSION#<token>, SK = SESSION#<token>`
- List all folders: `PK begins_with FOLDER#, SK begins_with FOLDER#` (via Scan with filter, or a GSI)
- List folders for user: `PK = USER#<username>, SK begins_with FOLDER#`
- List users for folder: GSI1 `GSI1PK = FOLDER#<folder_name>, GSI1SK begins_with USER#`
- List files in folder: `PK = FOLDER#<folder_name>, SK begins_with FILE#`
- List all users: Scan with `PK begins_with USER#, SK begins_with USER#`

## S3 Buckets

- **File bucket**: `fileshare-files-<account-id>` — private, no versioning
  - Object key pattern: `<folder_name>/<file_name>`
- **Static site bucket**: `fileshare-frontend-<account-id>` — public read, static website hosting enabled

## API Gateway Endpoints (Unit 1 scope)

- `POST /auth/login` — Login, returns session token
- `POST /auth/logout` — Logout, invalidates session
- `POST /auth/change-password` — Force password change on first login

## Lambda Functions (Unit 1 scope)

- `auth_handler` — Handles login, logout, password change
  - Consolidated: one Lambda, routes by HTTP method + path

### Auth Flow

1. Login: validate credentials against DDB → create session record with TTL → return token
2. Every subsequent request: Lambda checks `Authorization` header → looks up `SESSION#<token>` in DDB → rejects if missing/expired
3. Logout: delete session record from DDB
4. Force password change: if `force_password_change` is true, the login response includes a flag; the client must call change-password before accessing other endpoints

### Password Handling

- Passwords are hashed using Python's `hashlib` (SHA-256 with salt) before storage
- Default admin password is hardcoded in the seed script
- `force_password_change` flag is set to `true` for the seed admin account

### DynamoDB Decimal Handling

- A custom JSON encoder class converts `Decimal` to `int` or `float` before serialization
- Used in all Lambda response helpers

## SAM Template Structure

```
template.yaml
├── DynamoDB Table (FileShareTable + GSI1)
├── S3 File Bucket
├── S3 Frontend Bucket
├── API Gateway (RestApi)
├── Auth Lambda Function
└── IAM Roles / Policies
```

## React Front-End (Shell)

- Create React App with minimal structure
- Pages: Login, Dashboard (placeholder)
- API client utility configured with API Gateway base URL
- Session token stored in memory (or sessionStorage) and sent via `Authorization` header

## CORS

- API Gateway configured with CORS headers to allow requests from the static site bucket domain
