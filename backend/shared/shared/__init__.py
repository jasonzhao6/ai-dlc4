# Lambda Layer Structure
#
# backend/shared/
# └── python/
#     └── shared/
#         ├── __init__.py
#         ├── data_store.py      # DynamoDB single-table abstraction
#         ├── file_store.py      # S3 file bucket abstraction
#         ├── session_validator.py  # Session token validation
#         ├── access_control.py  # RBAC permission checks
#         └── json_encoder.py    # Decimal-safe JSON encoder + response helpers
#
# When deployed as a layer, Python imports work as:
#   from shared.data_store import DataStore
#   from shared.json_encoder import api_response
