# TODO — Post-Deployment Tasks

## Pre-Deploy Checklist
- [ ] Configure AWS credentials (`aws configure` or `aws sso login`)
- [ ] Set default region: `aws configure set region us-east-1` (or preferred region)

## Deploy Backend
```bash
cd /Users/yzhao/GitHub/jasonzhao6/ai-dlc4
sam build
sam deploy --guided
# Stack name suggestion: fileshare
# Note the outputs: ApiUrl, FrontendUrl, FrontendBucketName
```
- [ ] Run `sam build` from project root
- [ ] Run `sam deploy --guided` for first deploy
- [ ] Note the API URL from stack outputs
- [ ] Read CloudWatch Logs immediately: `sam logs --stack-name fileshare --tail`
- [ ] Verify admin seed ran: check DynamoDB for USER#admin record

## Deploy Frontend
```bash
# Set the API URL in the React build
cd frontend
REACT_APP_API_URL=<ApiUrl from outputs> npm run build
aws s3 sync build/ s3://<FrontendBucketName>/
```
- [ ] Set REACT_APP_API_URL and rebuild
- [ ] Upload build to frontend S3 bucket
- [ ] Verify app loads at FrontendUrl

## Integration Tests (run after full deploy)
Replace `$API` with the API Gateway URL from stack outputs.

### Auth (Unit 1)
```bash
# Login with default admin
curl -X POST $API/auth/login -d '{"username":"admin","password":"Admin123!"}'
# Should return: token + force_password_change: true

# Change password
TOKEN=<token from above>
curl -X POST $API/auth/change-password -H "Authorization: $TOKEN" -d '{"old_password":"Admin123!","new_password":"NewPass123!"}'

# Login with new password
curl -X POST $API/auth/login -d '{"username":"admin","password":"NewPass123!"}'

# Logout
curl -X POST $API/auth/logout -H "Authorization: $TOKEN"

# Access without token → 401
curl -X GET $API/users
```
- [ ] POST /auth/login with valid credentials → 200 + token
- [ ] POST /auth/login with invalid credentials → 401
- [ ] POST /auth/logout with valid token → 200
- [ ] POST /auth/change-password → 200
- [ ] Access protected endpoint without token → 401

### Users & Folders (Unit 2)
```bash
TOKEN=<admin token>

# Create folder
curl -X POST $API/folders -H "Authorization: $TOKEN" -d '{"folder_name":"test-folder"}'

# Create user with folder assignment
curl -X POST $API/users -H "Authorization: $TOKEN" -d '{"username":"uploader1","password":"Pass123!","role":"uploader","folder_names":["test-folder"]}'

# List users
curl -X GET $API/users -H "Authorization: $TOKEN"

# Update user
curl -X PUT $API/users/uploader1 -H "Authorization: $TOKEN" -d '{"role":"reader"}'

# Non-admin access → 403
UTOKEN=<uploader token>
curl -X POST $API/users -H "Authorization: $UTOKEN" -d '{"username":"x","password":"x","role":"viewer"}'
```
- [ ] POST /users as admin → 200
- [ ] POST /users as non-admin → 403
- [ ] GET /users as admin → 200
- [ ] PUT /users/{username} → 200
- [ ] DELETE /users/{username} → 200
- [ ] POST /folders as admin → 200
- [ ] GET /folders as admin → all; as non-admin → assigned only
- [ ] PUT /folders/{name} → 200
- [ ] DELETE /folders/{name} → 200

### Files & RBAC (Unit 3)
```bash
TOKEN=<uploader token>

# List files
curl -X GET "$API/folders/test-folder/files" -H "Authorization: $TOKEN"

# Request upload URL
curl -X POST "$API/folders/test-folder/files/upload" -H "Authorization: $TOKEN" -d '{"file_name":"test.txt","file_size":100}'

# Upload to S3 (use the upload_url from above)
curl -X PUT "<upload_url>" -d "hello world"

# Complete upload
curl -X POST "$API/folders/test-folder/files/upload/complete" -H "Authorization: $TOKEN" -d '{"file_name":"test.txt","file_size":100}'

# Download
curl -X POST "$API/folders/test-folder/files/test.txt/download" -H "Authorization: $TOKEN"
```
- [ ] GET /folders/{name}/files as assigned user → 200
- [ ] GET /folders/{name}/files as unassigned user → 403
- [ ] POST .../upload as uploader → 200
- [ ] POST .../upload as reader → 403
- [ ] POST .../upload as viewer → 403
- [ ] POST .../download as reader → 200
- [ ] POST .../download as viewer → 403
- [ ] Upload file > 1GB → 400
- [ ] Admin access any folder without assignment → 200

## Failed Actions Log
(Record any actions that fail during build and need retry after deploy)
- None so far. All code builds and SAM validates successfully.
