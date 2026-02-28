"""Shared test helpers — fakes and factory functions."""
import hashlib
import json
import secrets
import time


class FakeDataStore:
    """In-memory DynamoDB single-table fake for unit tests."""

    def __init__(self):
        self._items = {}

    def put_item(self, item):
        self._items[(item['PK'], item['SK'])] = dict(item)

    def get_item(self, pk, sk):
        return self._items.get((pk, sk))

    def delete_item(self, pk, sk):
        self._items.pop((pk, sk), None)

    def query_by_pk(self, pk, sk_prefix=None):
        results = []
        for (p, s), item in self._items.items():
            if p == pk and (sk_prefix is None or s.startswith(sk_prefix)):
                results.append(item)
        return results

    def query_gsi1(self, gsi1pk, gsi1sk_prefix=None):
        results = []
        for item in self._items.values():
            if item.get('GSI1PK') == gsi1pk:
                if gsi1sk_prefix is None or item.get('GSI1SK', '').startswith(gsi1sk_prefix):
                    results.append(item)
        return results

    def scan_by_pk_prefix(self, pk_prefix, sk_prefix=None):
        results = []
        for (p, s), item in self._items.items():
            if p.startswith(pk_prefix) and (sk_prefix is None or s.startswith(sk_prefix)):
                results.append(item)
        return results

    def batch_write(self, put_items=None, delete_keys=None):
        for item in (put_items or []):
            self.put_item(item)
        for key in (delete_keys or []):
            self.delete_item(key['PK'], key['SK'])


class FakeFileStore:
    """In-memory S3 fake for unit tests."""

    def __init__(self):
        self._objects = {}

    def generate_presigned_put_url(self, s3_key, expiry_seconds=900):
        return f'https://fake-s3.example.com/put/{s3_key}'

    def generate_presigned_get_url(self, s3_key, expiry_seconds=900):
        return f'https://fake-s3.example.com/get/{s3_key}'

    def copy_object(self, source_key, dest_key):
        self._objects[dest_key] = True

    def delete_object(self, s3_key):
        self._objects.pop(s3_key, None)

    def delete_by_prefix(self, prefix):
        for k in self.list_objects_by_prefix(prefix):
            self.delete_object(k)

    def list_objects_by_prefix(self, prefix):
        return [k for k in self._objects if k.startswith(prefix)]


def make_user_item(username, password, role, force_password_change=False):
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()
    return {
        'PK': f'USER#{username}', 'SK': f'USER#{username}',
        'username': username, 'password_hash': password_hash, 'salt': salt,
        'role': role, 'force_password_change': force_password_change,
        'created_at': int(time.time()),
    }


def make_session_item(token, username, role, ttl_offset=86400):
    now = int(time.time())
    return {
        'PK': f'SESSION#{token}', 'SK': f'SESSION#{token}',
        'username': username, 'role': role, 'created_at': now, 'ttl': now + ttl_offset,
    }


def make_folder_item(folder_name):
    return {
        'PK': f'FOLDER#{folder_name}', 'SK': f'FOLDER#{folder_name}',
        'folder_name': folder_name, 's3_prefix': f'{folder_name}/',
        'created_at': int(time.time()),
    }


def make_assignment_item(username, folder_name):
    return {
        'PK': f'USER#{username}', 'SK': f'FOLDER#{folder_name}',
        'GSI1PK': f'FOLDER#{folder_name}', 'GSI1SK': f'USER#{username}',
        'username': username, 'folder_name': folder_name,
        'assigned_at': int(time.time()),
    }


def make_file_item(folder_name, file_name, size=100, uploaded_by='admin'):
    return {
        'PK': f'FOLDER#{folder_name}', 'SK': f'FILE#{file_name}',
        'file_name': file_name, 'folder_name': folder_name,
        's3_key': f'{folder_name}/{file_name}', 'size': size,
        'uploaded_by': uploaded_by, 'uploaded_at': int(time.time()),
    }


def parse_response(resp):
    return resp['statusCode'], json.loads(resp['body'])


def make_event(method, path, body=None, token=None, path_params=None):
    event = {
        'httpMethod': method, 'path': path,
        'headers': {}, 'pathParameters': path_params,
        'body': json.dumps(body) if body else None,
    }
    if token:
        event['headers']['Authorization'] = token
    return event
