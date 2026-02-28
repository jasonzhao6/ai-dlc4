"""
Offline integration tests using real DynamoDB Local + S3 Mock (Docker).
No SAM Local — calls Lambda handlers directly in-process for speed.

Usage:
    docker compose up -d
    python -m pytest tests/integration/ -v

Requires: docker compose services running (dynamodb-local on 8033, s3-local on 9090)
"""
import os
import json
import time
import hashlib
import secrets
import pytest

# Point shared modules at local Docker services
os.environ['AWS_ACCESS_KEY_ID'] = 'fake'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fake'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['TABLE_NAME'] = 'test-table'
os.environ['FILE_BUCKET'] = 'test-files'
os.environ['DYNAMODB_ENDPOINT'] = 'http://127.0.0.1:8033'
os.environ['S3_ENDPOINT'] = 'http://127.0.0.1:9090'

import boto3
from shared.data_store import DataStore
from shared.file_store import FileStore
from shared.session_validator import SessionValidator
from shared.access_control import AccessControl

import backend.auth.handler as auth_mod
import backend.users.handler as users_mod
import backend.folders.handler as folders_mod
import backend.files.handler as files_mod


def is_docker_running():
    try:
        ds = DataStore()
        ds.scan_by_pk_prefix('HEALTHCHECK#')
        return True
    except Exception:
        return False


def parse(resp):
    return resp['statusCode'], json.loads(resp['body'])


def event(method, path, body=None, token=None, path_params=None):
    e = {
        'httpMethod': method, 'path': path,
        'headers': {}, 'pathParameters': path_params,
        'body': json.dumps(body) if body else None,
    }
    if token:
        e['headers']['Authorization'] = token
    return e


# ---- Fixtures ----

@pytest.fixture(scope='session', autouse=True)
def setup_local_services():
    if not is_docker_running():
        pytest.skip('Docker services not running. Run: docker compose up -d')

    ds = DataStore()

    # Wire all handlers to use real local DDB/S3
    for mod in [auth_mod, users_mod, folders_mod, files_mod]:
        mod.ds = ds
        mod.sv = SessionValidator(ds)
        if hasattr(mod, 'ac'):
            mod.ac = AccessControl(ds)
        if hasattr(mod, 'fs'):
            mod.fs = FileStore()

    # Seed admin
    existing = ds.get_item('USER#admin', 'USER#admin')
    if not existing:
        salt = secrets.token_hex(16)
        pw_hash = hashlib.sha256(f'{salt}Admin123!'.encode()).hexdigest()
        ds.put_item({
            'PK': 'USER#admin', 'SK': 'USER#admin',
            'username': 'admin', 'password_hash': pw_hash, 'salt': salt,
            'role': 'admin', 'force_password_change': False,
            'created_at': int(time.time()),
        })

    yield


@pytest.fixture(scope='session')
def admin_token():
    status, body = parse(auth_mod.lambda_handler(
        event('POST', '/auth/login', {'username': 'admin', 'password': 'Admin123!'}), None))
    assert status == 200, f'Admin login failed: {body}'
    return body['token']


@pytest.fixture(scope='module')
def test_folder(admin_token):
    name = f'inttest-{int(time.time())}'
    status, _ = parse(folders_mod.lambda_handler(
        event('POST', '/folders', {'folder_name': name}, token=admin_token), None))
    assert status == 200
    yield name
    folders_mod.lambda_handler(
        event('DELETE', f'/folders/{name}', token=admin_token,
              path_params={'folder_name': name}), None)


@pytest.fixture(scope='module')
def test_users(admin_token, test_folder):
    users = {}
    for role in ['uploader', 'reader', 'viewer']:
        uname = f'inttest-{role}-{int(time.time())}'
        status, _ = parse(users_mod.lambda_handler(
            event('POST', '/users', {
                'username': uname, 'password': 'TestPass1!', 'role': role,
                'folder_names': [test_folder],
            }, token=admin_token), None))
        assert status == 200

        status, body = parse(auth_mod.lambda_handler(
            event('POST', '/auth/login', {'username': uname, 'password': 'TestPass1!'}), None))
        assert status == 200
        users[role] = {'username': uname, 'token': body['token']}
        time.sleep(0.1)  # ensure unique timestamps

    yield users

    for info in users.values():
        users_mod.lambda_handler(
            event('DELETE', f'/users/{info["username"]}', token=admin_token,
                  path_params={'username': info['username']}), None)


# ---- Auth ----

class TestAuth:
    def test_login_valid(self):
        status, body = parse(auth_mod.lambda_handler(
            event('POST', '/auth/login', {'username': 'admin', 'password': 'Admin123!'}), None))
        assert status == 200
        assert 'token' in body

    def test_login_invalid(self):
        status, _ = parse(auth_mod.lambda_handler(
            event('POST', '/auth/login', {'username': 'admin', 'password': 'wrong'}), None))
        assert status == 401

    def test_no_token_401(self):
        status, _ = parse(users_mod.lambda_handler(
            event('GET', '/users'), None))
        assert status == 401

    def test_logout(self):
        status, body = parse(auth_mod.lambda_handler(
            event('POST', '/auth/login', {'username': 'admin', 'password': 'Admin123!'}), None))
        tok = body['token']
        status, _ = parse(auth_mod.lambda_handler(
            event('POST', '/auth/logout', token=tok), None))
        assert status == 200
        # Token invalid now
        status, _ = parse(users_mod.lambda_handler(
            event('GET', '/users', token=tok), None))
        assert status == 401


# ---- Users ----

class TestUsers:
    def test_list_users_admin(self, admin_token):
        status, body = parse(users_mod.lambda_handler(
            event('GET', '/users', token=admin_token), None))
        assert status == 200
        assert 'users' in body

    def test_list_users_non_admin(self, test_users):
        status, _ = parse(users_mod.lambda_handler(
            event('GET', '/users', token=test_users['viewer']['token']), None))
        assert status == 403

    def test_create_user_non_admin(self, test_users):
        status, _ = parse(users_mod.lambda_handler(
            event('POST', '/users', {'username': 'x', 'password': 'x', 'role': 'viewer'},
                  token=test_users['viewer']['token']), None))
        assert status == 403


# ---- Folders ----

class TestFolders:
    def test_list_folders_admin(self, admin_token, test_folder):
        status, body = parse(folders_mod.lambda_handler(
            event('GET', '/folders', token=admin_token), None))
        assert status == 200
        names = [f['folder_name'] for f in body['folders']]
        assert test_folder in names

    def test_non_admin_sees_assigned(self, test_users, test_folder):
        status, body = parse(folders_mod.lambda_handler(
            event('GET', '/folders', token=test_users['viewer']['token']), None))
        assert status == 200
        names = [f['folder_name'] for f in body['folders']]
        assert test_folder in names

    def test_create_folder_non_admin(self, test_users):
        status, _ = parse(folders_mod.lambda_handler(
            event('POST', '/folders', {'folder_name': 'nope'},
                  token=test_users['viewer']['token']), None))
        assert status == 403


# ---- Files & RBAC ----

class TestFiles:
    def test_list_files_assigned(self, test_users, test_folder):
        status, _ = parse(files_mod.lambda_handler(
            event('GET', f'/folders/{test_folder}/files',
                  token=test_users['viewer']['token'],
                  path_params={'folder_name': test_folder}), None))
        assert status == 200

    def test_list_files_unassigned(self, admin_token, test_users):
        name = f'unassigned-{int(time.time())}'
        folders_mod.lambda_handler(
            event('POST', '/folders', {'folder_name': name}, token=admin_token), None)
        status, _ = parse(files_mod.lambda_handler(
            event('GET', f'/folders/{name}/files',
                  token=test_users['viewer']['token'],
                  path_params={'folder_name': name}), None))
        assert status == 403
        folders_mod.lambda_handler(
            event('DELETE', f'/folders/{name}', token=admin_token,
                  path_params={'folder_name': name}), None)

    def test_upload_as_uploader(self, test_users, test_folder):
        tok = test_users['uploader']['token']
        status, body = parse(files_mod.lambda_handler(
            event('POST', f'/folders/{test_folder}/files/upload',
                  {'file_name': 'inttest.txt', 'file_size': 11},
                  token=tok, path_params={'folder_name': test_folder}), None))
        assert status == 200
        assert 'upload_url' in body

        # Complete upload metadata
        status, _ = parse(files_mod.lambda_handler(
            event('POST', f'/folders/{test_folder}/files/upload/complete',
                  {'file_name': 'inttest.txt', 'file_size': 11},
                  token=tok, path_params={'folder_name': test_folder}), None))
        assert status == 200

    def test_upload_as_reader_forbidden(self, test_users, test_folder):
        status, _ = parse(files_mod.lambda_handler(
            event('POST', f'/folders/{test_folder}/files/upload',
                  {'file_name': 'x.txt', 'file_size': 1},
                  token=test_users['reader']['token'],
                  path_params={'folder_name': test_folder}), None))
        assert status == 403

    def test_upload_as_viewer_forbidden(self, test_users, test_folder):
        status, _ = parse(files_mod.lambda_handler(
            event('POST', f'/folders/{test_folder}/files/upload',
                  {'file_name': 'x.txt', 'file_size': 1},
                  token=test_users['viewer']['token'],
                  path_params={'folder_name': test_folder}), None))
        assert status == 403

    def test_upload_too_large(self, test_users, test_folder):
        status, _ = parse(files_mod.lambda_handler(
            event('POST', f'/folders/{test_folder}/files/upload',
                  {'file_name': 'big.bin', 'file_size': 2_000_000_000},
                  token=test_users['uploader']['token'],
                  path_params={'folder_name': test_folder}), None))
        assert status == 400

    def test_download_as_reader(self, test_users, test_folder):
        status, body = parse(files_mod.lambda_handler(
            event('POST', f'/folders/{test_folder}/files/inttest.txt/download',
                  token=test_users['reader']['token'],
                  path_params={'folder_name': test_folder, 'file_name': 'inttest.txt'}), None))
        assert status == 200
        assert 'download_url' in body

    def test_download_as_viewer_forbidden(self, test_users, test_folder):
        status, _ = parse(files_mod.lambda_handler(
            event('POST', f'/folders/{test_folder}/files/inttest.txt/download',
                  token=test_users['viewer']['token'],
                  path_params={'folder_name': test_folder, 'file_name': 'inttest.txt'}), None))
        assert status == 403

    def test_admin_any_folder(self, admin_token, test_folder):
        status, _ = parse(files_mod.lambda_handler(
            event('GET', f'/folders/{test_folder}/files',
                  token=admin_token,
                  path_params={'folder_name': test_folder}), None))
        assert status == 200
