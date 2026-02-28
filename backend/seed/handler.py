import hashlib
import secrets
import time
import os
import json
import urllib.request

from shared.data_store import DataStore


def lambda_handler(event, context):
    """CloudFormation Custom Resource handler to seed admin account."""
    response_url = event.get('ResponseURL', '')
    request_type = event.get('RequestType', '')
    physical_id = 'SeedAdmin'

    try:
        if request_type == 'Create':
            seed_admin()
        # Update and Delete are no-ops
        send_cfn_response(event, response_url, 'SUCCESS', physical_id)
    except Exception as e:
        print(f'Error: {e}')
        send_cfn_response(event, response_url, 'FAILED', physical_id, str(e))


def seed_admin():
    ds = DataStore()
    username = os.environ.get('ADMIN_USERNAME', 'admin')
    password = os.environ.get('ADMIN_PASSWORD', 'Admin123!')

    # Check if admin already exists
    existing = ds.get_item(f'USER#{username}', f'USER#{username}')
    if existing:
        print(f'Admin user {username} already exists, skipping seed')
        return

    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()

    ds.put_item({
        'PK': f'USER#{username}',
        'SK': f'USER#{username}',
        'username': username,
        'password_hash': password_hash,
        'salt': salt,
        'role': 'admin',
        'force_password_change': True,
        'created_at': int(time.time()),
    })
    print(f'Admin user {username} seeded successfully')


def send_cfn_response(event, url, status, physical_id, reason=''):
    body = json.dumps({
        'Status': status,
        'Reason': reason,
        'PhysicalResourceId': physical_id,
        'StackId': event.get('StackId', ''),
        'RequestId': event.get('RequestId', ''),
        'LogicalResourceId': event.get('LogicalResourceId', ''),
    }).encode()

    req = urllib.request.Request(url, data=body, headers={'Content-Type': ''}, method='PUT')
    urllib.request.urlopen(req)
