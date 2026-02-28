# Unit 2: User & Folder Management — Design

## API Endpoints

### User Management

- `POST /users` — Create user (admin only)
- `GET /users` — List all users (admin only)
- `PUT /users/<username>` — Update user role/folder assignments (admin only)
- `DELETE /users/<username>` — Delete user (admin only)

### Folder Management

- `POST /folders` — Create folder (admin only)
- `GET /folders` — List folders (admin: all, others: assigned only)
- `PUT /folders/<folder_name>` — Rename folder (admin only)
- `DELETE /folders/<folder_name>` — Delete folder (admin only)

## Lambda Functions

- `users_handler` — Consolidated CRUD for users. Routes by HTTP method.
- `folders_handler` — Consolidated CRUD for folders. Routes by HTTP method.

Both Lambdas reuse the session validation helper from Unit 1 and check `role == "admin"` for all operations.

## DynamoDB Operations (Single-Table)

### Create User (`POST /users`)

1. Put `USER#<username> / USER#<username>` with `username`, `password_hash`, `role`, `created_at`
2. For each assigned folder, put `USER#<username> / FOLDER#<folder_name>` assignment record

### Update User (`PUT /users/<username>`)

1. Update `USER#<username> / USER#<username>` attributes (role)
2. Query existing assignments: `PK = USER#<username>, SK begins_with FOLDER#`
3. Diff with desired assignments → delete removed, put added

### Delete User (`DELETE /users/<username>`)

1. Delete `USER#<username> / USER#<username>`
2. Query and delete all `USER#<username> / FOLDER#<folder_name>` assignment records
3. Scan and delete all `SESSION#*` records where `username` matches (invalidate sessions)

### List Users (`GET /users`)

1. Scan where `PK begins_with USER#` and `SK begins_with USER#`
2. For each user, query `PK = USER#<username>, SK begins_with FOLDER#` to get assignments

### Create Folder (`POST /folders`)

1. Put `FOLDER#<folder_name> / FOLDER#<folder_name>` with `folder_name`, `s3_prefix`, `created_at`
2. Optionally create the S3 prefix (put a zero-byte object or just rely on first upload)

### Rename Folder (`PUT /folders/<folder_name>`)

1. Create new folder record `FOLDER#<new_name> / FOLDER#<new_name>`
2. Query all assignments via GSI1: `GSI1PK = FOLDER#<old_name>` → delete old, create new with `FOLDER#<new_name>`
3. Query all file metadata: `PK = FOLDER#<old_name>, SK begins_with FILE#` → recreate under `FOLDER#<new_name>`, delete old
4. Copy all S3 objects from `<old_name>/` to `<new_name>/`, then delete originals
5. Delete old folder record

### Delete Folder (`DELETE /folders/<folder_name>`)

1. Delete all S3 objects under `<folder_name>/`
2. Query and delete all file metadata: `PK = FOLDER#<folder_name>, SK begins_with FILE#`
3. Query and delete all assignments via GSI1: `GSI1PK = FOLDER#<folder_name>`
4. Delete folder record `FOLDER#<folder_name> / FOLDER#<folder_name>`

### List Folders (`GET /folders`)

- Admin: Scan where `PK begins_with FOLDER#` and `SK begins_with FOLDER#`
- Non-admin: Query `PK = USER#<username>, SK begins_with FOLDER#` to get assigned folder names, then batch-get folder records

## Admin Authorization

Every endpoint in this unit checks:
1. Valid session (reuse Unit 1 session validation)
2. `role == "admin"` (except `GET /folders` which returns filtered results for non-admins)
3. Return 403 Forbidden if not admin

## React Front-End

- Admin dashboard: User management page (list, create, update, delete users)
- Admin dashboard: Folder management page (list, create, rename, delete folders)
- User creation form includes role dropdown and folder multi-select
- Non-admin users see a folder list (their assigned folders) on the dashboard
