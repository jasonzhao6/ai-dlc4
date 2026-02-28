import json
import hashlib
import secrets
import time

from shared.data_store import DataStore
from shared.session_validator import SessionValidator
from shared.access_control import AccessControl
from shared.json_encoder import api_response

ds = DataStore()
sv = SessionValidator(ds)
ac = AccessControl(ds)


def lambda_handler(event, context):
    method = event.get('httpMethod', '')
    path = event.get('path', '')

    if method == 'OPTIONS':
        return api_response(200, {})

    user_info = sv.validate(event)
    if not user_info:
        return api_response(401, {'error': 'Unauthorized'})

    if method == 'POST' and path == '/users':
        return create_user(event, user_info)
    elif method == 'GET' and path == '/users':
        return list_users(user_info)
    elif method == 'PUT' and path.startswith('/users/'):
        return update_user(event, user_info)
    elif method == 'DELETE' and path.startswith('/users/'):
        return delete_user(event, user_info)

    return api_response(404, {'error': 'Not found'})


def create_user(event, user_info):
    if not ac.check_admin(user_info['role']):
        return api_response(403, {'error': 'Admin only'})

    body = json.loads(event.get('body') or '{}')
    username = body.get('username', '').strip()
    password = body.get('password', '')
    role = body.get('role', '')
    folder_names = body.get('folder_names', [])

    if not username or not password or role not in ('admin', 'uploader', 'reader', 'viewer'):
        return api_response(400, {'error': 'username, password, and valid role required'})

    existing = ds.get_item(f'USER#{username}', f'USER#{username}')
    if existing:
        return api_response(409, {'error': 'User already exists'})

    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()

    put_items = [{
        'PK': f'USER#{username}',
        'SK': f'USER#{username}',
        'username': username,
        'password_hash': password_hash,
        'salt': salt,
        'role': role,
        'force_password_change': False,
        'created_at': int(time.time()),
    }]

    for fn in folder_names:
        put_items.append({
            'PK': f'USER#{username}',
            'SK': f'FOLDER#{fn}',
            'GSI1PK': f'FOLDER#{fn}',
            'GSI1SK': f'USER#{username}',
            'username': username,
            'folder_name': fn,
            'assigned_at': int(time.time()),
        })

    ds.batch_write(put_items=put_items)
    return api_response(200, {'message': f'User {username} created'})


def list_users(user_info):
    if not ac.check_admin(user_info['role']):
        return api_response(403, {'error': 'Admin only'})

    users = ds.scan_by_pk_prefix('USER#', 'USER#')
    result = []
    for u in users:
        assignments = ds.query_by_pk(f'USER#{u["username"]}', 'FOLDER#')
        result.append({
            'username': u['username'],
            'role': u['role'],
            'folder_names': [a['folder_name'] for a in assignments],
            'created_at': u.get('created_at'),
        })

    return api_response(200, {'users': result})


def update_user(event, user_info):
    if not ac.check_admin(user_info['role']):
        return api_response(403, {'error': 'Admin only'})

    username = event['pathParameters']['username']
    body = json.loads(event.get('body') or '{}')

    user = ds.get_item(f'USER#{username}', f'USER#{username}')
    if not user:
        return api_response(404, {'error': 'User not found'})

    # Update role if provided
    new_role = body.get('role')
    if new_role and new_role in ('admin', 'uploader', 'reader', 'viewer'):
        user['role'] = new_role
        ds.put_item(user)

    # Update folder assignments if provided
    new_folders = body.get('folder_names')
    if new_folders is not None:
        existing = ds.query_by_pk(f'USER#{username}', 'FOLDER#')
        existing_names = {a['folder_name'] for a in existing}
        desired_names = set(new_folders)

        to_delete = existing_names - desired_names
        to_add = desired_names - existing_names

        delete_keys = [{'PK': f'USER#{username}', 'SK': f'FOLDER#{fn}'} for fn in to_delete]
        put_items = [{
            'PK': f'USER#{username}',
            'SK': f'FOLDER#{fn}',
            'GSI1PK': f'FOLDER#{fn}',
            'GSI1SK': f'USER#{username}',
            'username': username,
            'folder_name': fn,
            'assigned_at': int(time.time()),
        } for fn in to_add]

        ds.batch_write(put_items=put_items, delete_keys=delete_keys)

    return api_response(200, {'message': f'User {username} updated'})


def delete_user(event, user_info):
    if not ac.check_admin(user_info['role']):
        return api_response(403, {'error': 'Admin only'})

    username = event['pathParameters']['username']

    user = ds.get_item(f'USER#{username}', f'USER#{username}')
    if not user:
        return api_response(404, {'error': 'User not found'})

    # Delete user record
    ds.delete_item(f'USER#{username}', f'USER#{username}')

    # Delete folder assignments
    assignments = ds.query_by_pk(f'USER#{username}', 'FOLDER#')
    delete_keys = [{'PK': f'USER#{username}', 'SK': a['SK']} for a in assignments]
    if delete_keys:
        ds.batch_write(delete_keys=delete_keys)

    # Invalidate sessions
    sessions = ds.scan_by_pk_prefix('SESSION#', 'SESSION#')
    session_keys = [{'PK': s['PK'], 'SK': s['SK']} for s in sessions if s.get('username') == username]
    if session_keys:
        ds.batch_write(delete_keys=session_keys)

    return api_response(200, {'message': f'User {username} deleted'})
