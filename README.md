# S3 File-Sharing System

A web-based file-sharing system backed by S3, with DynamoDB for state management and role-based access control.

## Prerequisites

- Python 3.12+
- Node.js 18+
- AWS SAM CLI
- AWS credentials configured

## Tests

### Unit Tests

Run locally with no AWS credentials needed:

```bash
pip install pytest
python -m pytest tests/unit/ -v
```

### Integration Tests

Run against a deployed API Gateway:

```bash
API_URL=https://xxx.execute-api.us-east-1.amazonaws.com/prod python -m pytest tests/integration/ -v
```

Integration tests create temporary users/folders and clean up after themselves.

### All Tests

```bash
python -m pytest -v
```

Without `API_URL` set, integration tests are automatically skipped.
