# S3 File-Sharing System

A web-based file-sharing system backed by S3, with DynamoDB for state management and role-based access control.

## Prerequisites

- Python 3.12+
- Node.js 18+
- Docker
- AWS SAM CLI (for deployment only)

## Run Locally

```bash
# Start local DynamoDB + S3
docker compose up -d

# Install Python deps
pip install flask flask-cors

# Build React frontend
cd frontend && REACT_APP_API_URL=http://localhost:5000 npm run build && cd ..

# Start the app
python scripts/local_server.py
```

Open http://localhost:5000 and login with `admin` / `Admin123!`

## Tests

### Unit Tests (no dependencies)

```bash
pip install pytest
python -m pytest tests/unit/ -v
```

63 tests, ~5s, no Docker or AWS needed.

### Integration Tests (offline, requires Docker)

```bash
bash scripts/integration_test_local.sh
```

19 tests, ~2s. Uses real DynamoDB Local + S3 Mock in Docker.

### All Tests

```bash
docker compose up -d
python -m pytest -v
```

Without Docker, integration tests are automatically skipped.
