#!/bin/bash
# Lambda Layer Structure Verification Script
#
# Source structure (before SAM build):
#   backend/shared/
#   └── shared/
#       ├── __init__.py
#       ├── data_store.py
#       ├── file_store.py
#       ├── session_validator.py
#       ├── access_control.py
#       └── json_encoder.py
#
# Built structure (after sam build, with BuildMethod: python3.12):
#   .aws-sam/build/SharedLayer/
#   └── python/
#       └── shared/
#           ├── __init__.py
#           ├── ...
#
# Lambda functions import via:
#   from shared.data_store import DataStore

set -e
LAYER_DIR="backend/shared/shared"

REQUIRED_FILES=(
  "__init__.py"
  "data_store.py"
  "file_store.py"
  "session_validator.py"
  "access_control.py"
  "json_encoder.py"
)

echo "Verifying Lambda layer source structure..."
ERRORS=0

if [ ! -d "$LAYER_DIR" ]; then
  echo "FAIL: Directory $LAYER_DIR does not exist"
  exit 1
fi

for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$LAYER_DIR/$f" ]; then
    echo "FAIL: Missing $LAYER_DIR/$f"
    ERRORS=$((ERRORS + 1))
  else
    echo "  OK: $LAYER_DIR/$f"
  fi
done

# Verify built structure if .aws-sam exists
if [ -d ".aws-sam/build/SharedLayer/python/shared" ]; then
  echo ""
  echo "Verifying built layer structure..."
  for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f ".aws-sam/build/SharedLayer/python/shared/$f" ]; then
      echo "FAIL: Missing built .aws-sam/build/SharedLayer/python/shared/$f"
      ERRORS=$((ERRORS + 1))
    else
      echo "  OK: .aws-sam/build/SharedLayer/python/shared/$f"
    fi
  done
fi

if [ $ERRORS -eq 0 ]; then
  echo ""
  echo "Layer structure verification PASSED"
else
  echo ""
  echo "Layer structure verification FAILED ($ERRORS errors)"
  exit 1
fi
