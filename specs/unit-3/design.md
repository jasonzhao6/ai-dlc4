# Unit 3: File Operations & RBAC — Design

## API Endpoints

- `GET /folders/<folder_name>/files` — List files in a folder (all roles with access)
- `POST /folders/<folder_name>/files/upload` — Get pre-signed upload URL (admin, uploader only)
- `POST /folders/<folder_name>/files/upload/complete` — Record file metadata after upload completes
- `POST /folders/<folder_name>/files/<file_name>/download` — Get pre-signed download URL (admin, uploader, reader only)

## Lambda Function

- `files_handler` — Consolidated handler for all file operations. Routes by HTTP method + path.

## RBAC Enforcement

The `files_handler` implements a permission check on every request:

1. Validate session (reuse Unit 1 helper) → get `username` and `role`
2. Check folder access: query `PK = USER#<username>, SK = FOLDER#<folder_name>` — must exist (unless admin)
3. Check action permission based on role:

**Permission matrix:**

- admin: view ✅, upload ✅, download ✅ (all folders, no assignment needed)
- uploader: view ✅, upload ✅, download ✅ (assigned folders only)
- reader: view ✅, upload ❌, download ✅ (assigned folders only)
- viewer: view ✅, upload ❌, download ❌ (assigned folders only)

Return 403 if the role doesn't permit the action, or if the user isn't assigned to the folder.

## File Upload Flow

1. Client calls `POST /folders/<folder_name>/files/upload` with `{ "file_name": "...", "file_size": ... }`
2. Lambda checks: session valid, folder assigned, role is admin or uploader, file_size ≤ 1GB
3. Lambda generates a pre-signed S3 PUT URL for key `<folder_name>/<file_name>` (expiry: 15 min)
4. Lambda returns `{ "upload_url": "...", "s3_key": "..." }`
5. Client uploads directly to S3 using the pre-signed URL
6. Client calls `POST /folders/<folder_name>/files/upload/complete` with `{ "file_name": "...", "file_size": ... }`
7. Lambda writes file metadata to DDB: `PK = FOLDER#<folder_name>, SK = FILE#<file_name>`

## File Download Flow

1. Client calls `POST /folders/<folder_name>/files/<file_name>/download`
2. Lambda checks: session valid, folder assigned, role is admin/uploader/reader
3. Lambda generates a pre-signed S3 GET URL for key `<folder_name>/<file_name>` (expiry: 15 min)
4. Lambda returns `{ "download_url": "..." }`
5. Client downloads directly from S3

## List Files Flow

1. Client calls `GET /folders/<folder_name>/files`
2. Lambda checks: session valid, folder assigned (or admin)
3. Lambda queries DDB: `PK = FOLDER#<folder_name>, SK begins_with FILE#`
4. Returns list of `{ file_name, size, uploaded_by, uploaded_at }`

## React Front-End

- Folder detail page: shows file list with name, size, upload date
- Upload button (visible to admin and uploader only): triggers pre-signed upload flow
- Download button per file (visible to admin, uploader, reader only): triggers pre-signed download
- Viewer sees file list but no upload or download buttons
