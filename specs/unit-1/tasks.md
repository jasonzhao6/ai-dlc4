# Unit 1: Foundation & Auth — Tasks

## Infrastructure

- [x] 1. Create SAM `template.yaml` with DynamoDB table (PK, SK, GSI1, TTL on `ttl` attribute)
- [x] 2. Add S3 file bucket (private, no versioning) to SAM template
- [x] 3. Add S3 frontend bucket (public read, static website hosting) to SAM template
- [x] 4. Add API Gateway RestApi resource to SAM template with CORS configuration
- [x] 5. Create shared Python utility: DynamoDB Decimal-safe JSON encoder

## Auth Lambda

- [x] 6. Create `auth_handler` Lambda function with route dispatch (login, logout, change-password)
- [x] 7. Implement `POST /auth/login` — validate credentials, create session in DDB, return token
- [x] 8. Implement `POST /auth/logout` — delete session record from DDB
- [x] 9. Implement `POST /auth/change-password` — update password hash, clear `force_password_change` flag
- [x] 10. Implement session validation helper — lookup `SESSION#<token>`, check TTL, return user info or 401

## Admin Seed

- [x] 11. Create seed script to insert default admin user into DDB with hardcoded password (hashed) and `force_password_change: true`
- [x] 12. Wire seed script into SAM deployment (custom resource or post-deploy script)

## React Front-End Shell

- [x] 13. Initialize React app with login page and dashboard placeholder
- [x] 14. Create API client utility with base URL config and `Authorization` header injection
- [x] 15. Implement login flow: call `/auth/login`, store token, redirect to dashboard
- [x] 16. Implement forced password change flow: detect flag, show change-password form before dashboard
- [x] 17. Implement logout: call `/auth/logout`, clear token, redirect to login

## Integration Tests

- [ ] 18. HTTPS test: `POST /auth/login` with valid credentials → 200 + token
- [ ] 19. HTTPS test: `POST /auth/login` with invalid credentials → 401
- [ ] 20. HTTPS test: `POST /auth/logout` with valid token → 200
- [ ] 21. HTTPS test: `POST /auth/change-password` → 200, then login with new password succeeds
- [ ] 22. HTTPS test: Access protected endpoint without token → 401

## Deploy

- [ ] 23. `sam build` and `sam deploy` (no containers, local Python version)
- [ ] 24. Upload React build to frontend S3 bucket
- [ ] 25. Verify app loads in browser and login works end-to-end
