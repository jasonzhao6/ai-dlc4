# S3 File-Sharing System

A web-based file-sharing system backed by S3, with DynamoDB for state management and role-based access control.

## Prerequisites

- Python 3.12+
- Node.js 18+
- AWS SAM CLI
- Docker (for integration tests)

## Tests

### Unit Tests (no dependencies)

```bash
pip install pytest
python -m pytest tests/unit/ -v
```

63 tests, runs in ~5s, no AWS credentials or Docker needed.

### Integration Tests (fully offline, requires Docker)

```bash
bash scripts/integration_test_local.sh
```

19 tests, runs in ~2s. Starts DynamoDB Local + S3 Mock in Docker, runs handlers against real services, cleans up after.

### All Tests

```bash
docker compose up -d
python -m pytest -v
```

Without Docker running, integration tests are automatically skipped.
