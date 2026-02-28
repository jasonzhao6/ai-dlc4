"""
Integration tests for the S3 File-Sharing System.

Run against a deployed API Gateway:
    API_URL=https://xxx.execute-api.us-east-1.amazonaws.com/prod pytest tests/integration/ -v

These tests create real data in DynamoDB and S3. They clean up after themselves.
"""
import os
import json
import time
import requests
import pytest

API_URL = os.environ.get('API_URL', '')


def skip_if_no_api():
    if not API_URL:
        pytest.skip('API_URL not set — skipping integration tests')


# ---- Helpers ----

def post(path, body=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = token
    return requests.post(f'{API_URL}{path}', json=body, headers=headers)


def get(path, token=None):
    headers = {}
    if token:
        headers['Authorization'] = token
    return requests.get(f'{API_URL}{path}', headers=headers)


def put(path, body=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = token
    return requests.put(f'{API_URL}{path}', json=body, headers=headers)


def delete(path, token=None):
    headers = {}
    if token:
        headers['Authorization'] = token
    return requests.delete(f'{API_URL}{path}', headers=headers)


def admin_login():
    """Login as admin. Assumes admin account exists with known password."""
    # Try default password first, then changed password
    for pw in ['Admin123!', 'IntTestPass1!']:
        r = post('/auth/login', {'username': 'admin', 'password': pw})
        if r.status_code == 200:
            data = r.json()
            if data.get('force_password_change'):
                # Change password
                tok = data['token']
                post('/auth/change-password',
                     {'old_password': pw, 'new_password': 'IntTestPass1!'}, token=tok)
                r = post('/auth/login', {'username': 'admin', 'password': 'IntTestPass1!'})
            return r.json()['token']
    raise RuntimeError('Cannot login as admin')


# ---- Fixtures ----

@pytest.fixture(scope='module')
def admin_token():
    skip_if_no_api()
    return admin_login()


@pytest.fixture(scope='module')
def test_folder(admin_token):
    """Create a test folder, yield its name, delete it after."""
    name = f'inttest-{int(time.time())}'
    r = post('/folders', {'folder_name': name}, token=admin_token)
    assert r.status_code == 200
    yield name
    delete(f'/folders/{name}', token=admin_token)


@pytest.fixture(scope='module')
def test_users(admin_token, test_folder):
    """Create test users for each role, yield dict of role->token, clean up."""
    users = {}
    for role in ['uploader', 'reader', 'viewer']:
        uname = f'inttest-{role}-{int(time.time())}'
        r = post('/users', {
            'username': uname, 'password': 'TestPass1!', 'role': role,
            'folder_names': [test_folder],
        }, token=admin_token)
        assert r.status_code == 200
        r = post('/auth/login', {'username': uname, 'password': 'TestPass1!'})
        assert r.status_code == 200
        users[role] = {'username': uname, 'token': r.json()['token']}

    yield users

    for role, info in users.items():
        post('/auth/logout', token=info['token'])
        delete(f'/users/{info["username"]}', token=admin_token)


# ---- Auth Tests ----

class TestAuth:
    def test_login_valid(self):
        skip_if_no_api()
        r = post('/auth/login', {'username': 'admin', 'password': 'IntTestPass1!'})
        assert r.status_code == 200
        assert 'token' in r.json()

    def test_login_invalid(self):
        skip_if_no_api()
        r = post('/auth/login', {'username': 'admin', 'password': 'wrong'})
        assert r.status_code == 401

    def test_no_token_401(self):
        skip_if_no_api()
        r = get('/users')
        assert r.status_code == 401

    def test_logout(self):
        skip_if_no_api()
        r = post('/auth/login', {'username': 'admin', 'password': 'IntTestPass1!'})
        tok = r.json()['token']
        r = post('/auth/logout', token=tok)
        assert r.status_code == 200
        # Token should be invalid now
        r = get('/users', token=tok)
        assert r.status_code == 401


# ---- User Management Tests ----

class TestUsers:
    def test_list_users_admin(self, admin_token):
        r = get('/users', token=admin_token)
        assert r.status_code == 200
        assert 'users' in r.json()

    def test_list_users_non_admin(self, test_users):
        r = get('/users', token=test_users['viewer']['token'])
        assert r.status_code == 403

    def test_create_user_non_admin(self, test_users):
        r = post('/users', {'username': 'x', 'password': 'x', 'role': 'viewer'},
                 token=test_users['viewer']['token'])
        assert r.status_code == 403


# ---- Folder Management Tests ----

class TestFolders:
    def test_list_folders_admin(self, admin_token, test_folder):
        r = get('/folders', token=admin_token)
        assert r.status_code == 200
        names = [f['folder_name'] for f in r.json()['folders']]
        assert test_folder in names

    def test_list_folders_non_admin_sees_assigned(self, test_users, test_folder):
        r = get('/folders', token=test_users['viewer']['token'])
        assert r.status_code == 200
        names = [f['folder_name'] for f in r.json()['folders']]
        assert test_folder in names

    def test_create_folder_non_admin(self, test_users):
        r = post('/folders', {'folder_name': 'nope'}, token=test_users['viewer']['token'])
        assert r.status_code == 403


# ---- File Operations & RBAC Tests ----

class TestFiles:
    def test_list_files_assigned(self, test_users, test_folder):
        r = get(f'/folders/{test_folder}/files', token=test_users['viewer']['token'])
        assert r.status_code == 200

    def test_list_files_unassigned(self, admin_token, test_users):
        # Create a folder the viewer is NOT assigned to
        name = f'unassigned-{int(time.time())}'
        post('/folders', {'folder_name': name}, token=admin_token)
        r = get(f'/folders/{name}/files', token=test_users['viewer']['token'])
        assert r.status_code == 403
        delete(f'/folders/{name}', token=admin_token)

    def test_upload_as_uploader(self, test_users, test_folder):
        tok = test_users['uploader']['token']
        r = post(f'/folders/{test_folder}/files/upload',
                 {'file_name': 'inttest.txt', 'file_size': 11}, token=tok)
        assert r.status_code == 200
        assert 'upload_url' in r.json()

        # Upload to S3
        upload_url = r.json()['upload_url']
        s3r = requests.put(upload_url, data=b'hello world')
        assert s3r.status_code == 200

        # Complete
        r = post(f'/folders/{test_folder}/files/upload/complete',
                 {'file_name': 'inttest.txt', 'file_size': 11}, token=tok)
        assert r.status_code == 200

    def test_upload_as_reader_forbidden(self, test_users, test_folder):
        r = post(f'/folders/{test_folder}/files/upload',
                 {'file_name': 'x.txt', 'file_size': 1},
                 token=test_users['reader']['token'])
        assert r.status_code == 403

    def test_upload_as_viewer_forbidden(self, test_users, test_folder):
        r = post(f'/folders/{test_folder}/files/upload',
                 {'file_name': 'x.txt', 'file_size': 1},
                 token=test_users['viewer']['token'])
        assert r.status_code == 403

    def test_upload_too_large(self, test_users, test_folder):
        r = post(f'/folders/{test_folder}/files/upload',
                 {'file_name': 'big.bin', 'file_size': 2_000_000_000},
                 token=test_users['uploader']['token'])
        assert r.status_code == 400

    def test_download_as_reader(self, test_users, test_folder):
        r = post(f'/folders/{test_folder}/files/inttest.txt/download',
                 token=test_users['reader']['token'])
        assert r.status_code == 200
        assert 'download_url' in r.json()

    def test_download_as_viewer_forbidden(self, test_users, test_folder):
        r = post(f'/folders/{test_folder}/files/inttest.txt/download',
                 token=test_users['viewer']['token'])
        assert r.status_code == 403

    def test_admin_any_folder(self, admin_token, test_folder):
        r = get(f'/folders/{test_folder}/files', token=admin_token)
        assert r.status_code == 200
