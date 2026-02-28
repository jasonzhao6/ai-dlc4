import json
import hashlib
import secrets
import time
import os

from shared.data_store import DataStore
from shared.session_validator import SessionValidator
from shared.json_encoder import api_response

SESSION_TTL = 86400  # 24 hours

ds = DataStore()
sv = SessionValidator(ds)


def lambda_handler(event, context):
    path = event.get('path', '')
    method = event.get('httpMethod', '')

    if method == 'OPTIONS':
        return api_response(200, {})

    if path == '/auth/login' and method == 'POST':
        return handle_login(event)
    elif path == '/auth/logout' and method == 'POST':
        return handle_logout(event)
    elif path == '/auth/change-password' and method == 'POST':
        return handle_change_password(event)

    return api_response(404, {'error': 'Not found'})


def handle_login(event):
    body = json.loads(event.get('body') or '{}')
    username = body.get('username', '')
    password = body.get('password', '')

    if not username or not password:
        return api_response(400, {'error': 'Username and password required'})

    user = ds.get_item(f'USER#{username}', f'USER#{username}')
    if not user:
        return api_response(401, {'error': 'Invalid credentials'})

    salt = user.get('salt', '')
    expected_hash = user.get('password_hash', '')
    provided_hash = hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()

    if provided_hash != expected_hash:
        return api_response(401, {'error': 'Invalid credentials'})

    token = secrets.token_hex(32)
    now = int(time.time())
    ds.put_item({
        'PK': f'SESSION#{token}',
        'SK': f'SESSION#{token}',
        'username': username,
        'role': user['role'],
        'created_at': now,
        'ttl': now + SESSION_TTL,
    })

    return api_response(200, {
        'token': token,
        'username': username,
        'role': user['role'],
        'force_password_change': user.get('force_password_change', False),
    })


def handle_logout(event):
    user_info = sv.validate(event)
    if not user_info:
        return api_response(401, {'error': 'Unauthorized'})

    ds.delete_item(f'SESSION#{user_info["token"]}', f'SESSION#{user_info["token"]}')
    return api_response(200, {'message': 'Logged out'})


def handle_change_password(event):
    user_info = sv.validate(event)
    if not user_info:
        return api_response(401, {'error': 'Unauthorized'})

    body = json.loads(event.get('body') or '{}')
    old_password = body.get('old_password', '')
    new_password = body.get('new_password', '')

    if not old_password or not new_password:
        return api_response(400, {'error': 'Old and new passwords required'})

    user = ds.get_item(f'USER#{user_info["username"]}', f'USER#{user_info["username"]}')
    if not user:
        return api_response(404, {'error': 'User not found'})

    salt = user.get('salt', '')
    expected_hash = user.get('password_hash', '')
    provided_hash = hashlib.sha256(f'{salt}{old_password}'.encode()).hexdigest()

    if provided_hash != expected_hash:
        return api_response(401, {'error': 'Invalid old password'})

    new_salt = secrets.token_hex(16)
    new_hash = hashlib.sha256(f'{new_salt}{new_password}'.encode()).hexdigest()

    ds.put_item({
        **user,
        'password_hash': new_hash,
        'salt': new_salt,
        'force_password_change': False,
    })

    return api_response(200, {'message': 'Password changed'})
