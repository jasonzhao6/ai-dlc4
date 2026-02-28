# Unit 3: File Operations & RBAC — Tasks

## Backend — Files Lambda

- [x] 1. Create `files_handler` Lambda with route dispatch
- [x] 2. Implement RBAC helper: check session → check folder assignment → check role permission
- [x] 3. Implement `GET /folders/<folder_name>/files` — list file metadata from DDB
- [x] 4. Implement `POST /folders/<folder_name>/files/upload` — validate role/size, generate pre-signed PUT URL
- [x] 5. Implement `POST /folders/<folder_name>/files/upload/complete` — write file metadata to DDB
- [x] 6. Implement `POST /folders/<folder_name>/files/<file_name>/download` — validate role, generate pre-signed GET URL
- [x] 7. Add `files_handler` Lambda + API Gateway routes to SAM template

## React Front-End

- [x] 8. Build folder detail page: file list with name, size, upload date columns
- [x] 9. Implement upload flow: request pre-signed URL → upload to S3 → call complete endpoint
- [x] 10. Implement download flow: request pre-signed URL → trigger browser download
- [x] 11. Conditionally show/hide upload button based on user role (admin, uploader only)
- [x] 12. Conditionally show/hide download button based on user role (admin, uploader, reader only)

## Integration Tests

- [ ] 13. HTTPS test: `GET /folders/<folder>/files` as assigned user → 200, file list
- [ ] 14. HTTPS test: `GET /folders/<folder>/files` as unassigned user → 403
- [ ] 15. HTTPS test: `POST .../upload` as uploader → 200, pre-signed URL returned
- [ ] 16. HTTPS test: `POST .../upload` as reader → 403
- [ ] 17. HTTPS test: `POST .../upload` as viewer → 403
- [ ] 18. HTTPS test: `POST .../download` as reader → 200, pre-signed URL returned
- [ ] 19. HTTPS test: `POST .../download` as viewer → 403
- [ ] 20. HTTPS test: Upload file > 1GB → 400 rejected
- [ ] 21. HTTPS test: Admin can access any folder's files without assignment → 200

## Deploy

- [ ] 22. `sam build` and `sam deploy`
- [ ] 23. Upload updated React build to frontend S3 bucket
- [ ] 24. Verify upload/download/view works end-to-end with each role
