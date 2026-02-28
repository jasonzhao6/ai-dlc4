#!/bin/bash
# Run integration tests fully offline.
# Calls Lambda handlers in-process against real DynamoDB Local + S3 Mock.
#
# Usage: bash scripts/integration_test_local.sh

set -e
cd "$(dirname "$0")/.."

cleanup() {
  echo ""
  echo "Cleaning up..."
  docker compose down 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Starting Docker services ==="
docker compose up -d
sleep 3

echo "=== Verifying DynamoDB Local ==="
export AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake AWS_DEFAULT_REGION=us-east-1
until aws dynamodb list-tables --endpoint-url http://127.0.0.1:8033 --region us-east-1 --no-cli-pager >/dev/null 2>&1; do
  sleep 1
done
echo "  Ready"

echo "=== Creating DynamoDB table ==="
aws dynamodb create-table \
  --endpoint-url http://127.0.0.1:8033 --region us-east-1 \
  --table-name test-table \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S AttributeName=GSI1SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
    'IndexName=GSI1,KeySchema=[{AttributeName=GSI1PK,KeyType=HASH},{AttributeName=GSI1SK,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
  --billing-mode PAY_PER_REQUEST --no-cli-pager 2>/dev/null && echo "  Created" || echo "  Already exists"

echo ""
echo "=== Running integration tests ==="
python -m pytest tests/integration/ -v
