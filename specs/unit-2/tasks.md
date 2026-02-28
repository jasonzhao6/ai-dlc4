# Unit 2: User & Folder Management — Tasks

## Backend — Users Lambda

- [ ] 1. Create `users_handler` Lambda with route dispatch (POST, GET, PUT, DELETE)
- [ ] 2. Implement `POST /users` — create user record + folder assignment records in DDB
- [ ] 3. Implement `GET /users` — scan users, query their folder assignments
- [ ] 4. Implement `PUT /users/<username>` — update role, diff and update folder assignments
- [ ] 5. Implement `DELETE /users/<username>` — delete user record, assignments, and active sessions
- [ ] 6. Add admin authorization check to all user endpoints (403 if not admin)
- [ ] 7. Add `users_handler` Lambda + API Gateway routes to SAM template

## Backend — Folders Lambda

- [ ] 8. Create `folders_handler` Lambda with route dispatch (POST, GET, PUT, DELETE)
- [ ] 9. Implement `POST /folders` — create folder record in DDB
- [ ] 10. Implement `GET /folders` — admin gets all, non-admin gets assigned folders only
- [ ] 11. Implement `PUT /folders/<folder_name>` — rename folder record, reassign assignments, move S3 objects, update file metadata
- [ ] 12. Implement `DELETE /folders/<folder_name>` — delete S3 objects, file metadata, assignments, and folder record
- [ ] 13. Add admin authorization check to create/rename/delete (403 if not admin)
- [ ] 14. Add `folders_handler` Lambda + API Gateway routes to SAM template

## React Front-End

- [ ] 15. Build admin user management page (list, create, update, delete)
- [ ] 16. Build admin folder management page (list, create, rename, delete)
- [ ] 17. Build folder list view for non-admin users (shows assigned folders only)

## Integration Tests

- [ ] 18. HTTPS test: `POST /users` as admin → 200, user created
- [ ] 19. HTTPS test: `POST /users` as non-admin → 403
- [ ] 20. HTTPS test: `GET /users` as admin → 200, returns user list
- [ ] 21. HTTPS test: `PUT /users/<username>` → 200, role/assignments updated
- [ ] 22. HTTPS test: `DELETE /users/<username>` → 200, user removed, sessions invalidated
- [ ] 23. HTTPS test: `POST /folders` as admin → 200, folder created
- [ ] 24. HTTPS test: `GET /folders` as admin → all folders; as non-admin → assigned only
- [ ] 25. HTTPS test: `PUT /folders/<folder_name>` → 200, folder renamed, S3 objects moved
- [ ] 26. HTTPS test: `DELETE /folders/<folder_name>` → 200, folder and contents removed

## Deploy

- [ ] 27. `sam build` and `sam deploy`
- [ ] 28. Upload updated React build to frontend S3 bucket
- [ ] 29. Verify user and folder management works end-to-end in browser
