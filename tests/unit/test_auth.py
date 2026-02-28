"""Unit tests for auth Lambda handler."""
import os
import pytest

os.environ.setdefault('TABLE_NAME', 'test-table')
os.environ.setdefault('FILE_BUCKET', 'test-bucket')

from tests.helpers import (
    FakeDataStore, make_user_item, make_session_item, parse_response, make_event,
)
import backend.auth.handler as auth_mod
from shared.session_validator import SessionValidator


@pytest.fixture(autouse=True)
def patch_auth(fake_ds):
    auth_mod.ds = fake_ds
    auth_mod.sv = SessionValidator(fake_ds)
    yield


@pytest.fixture
def admin_user(fake_ds):
    item = make_user_item('admin', 'Admin123!', 'admin', force_password_change=True)
    fake_ds.put_item(item)
    return item


class TestLogin:
    def test_success(self, admin_user):
        event = make_event('POST', '/auth/login', {'username': 'admin', 'password': 'Admin123!'})
        status, body = parse_response(auth_mod.lambda_handler(event, None))
        assert status == 200
        assert 'token' in body
        assert body['role'] == 'admin'
        assert body['force_password_change'] is True

    def test_wrong_password(self, admin_user):
        event = make_event('POST', '/auth/login', {'username': 'admin', 'password': 'wrong'})
        status, _ = parse_response(auth_mod.lambda_handler(event, None))
        assert status == 401

    def test_nonexistent_user(self):
        event = make_event('POST', '/auth/login', {'username': 'nobody', 'password': 'x'})
        status, _ = parse_response(auth_mod.lambda_handler(event, None))
        assert status == 401

    def test_missing_fields(self):
        event = make_event('POST', '/auth/login', {'username': ''})
        status, _ = parse_response(auth_mod.lambda_handler(event, None))
        assert status == 400

    def test_creates_session(self, fake_ds, admin_user):
        event = make_event('POST', '/auth/login', {'username': 'admin', 'password': 'Admin123!'})
        _, body = parse_response(auth_mod.lambda_handler(event, None))
        assert fake_ds.get_item(f'SESSION#{body["token"]}', f'SESSION#{body["token"]}') is not None


class TestLogout:
    def test_success(self, fake_ds, admin_user):
        _, body = parse_response(auth_mod.lambda_handler(
            make_event('POST', '/auth/login', {'username': 'admin', 'password': 'Admin123!'}), None))
        token = body['token']
        status, _ = parse_response(auth_mod.lambda_handler(
            make_event('POST', '/auth/logout', token=token), None))
        assert status == 200
        assert fake_ds.get_item(f'SESSION#{token}', f'SESSION#{token}') is None

    def test_no_token(self):
        status, _ = parse_response(auth_mod.lambda_handler(
            make_event('POST', '/auth/logout'), None))
        assert status == 401


class TestChangePassword:
    def test_success(self, fake_ds, admin_user):
        _, body = parse_response(auth_mod.lambda_handler(
            make_event('POST', '/auth/login', {'username': 'admin', 'password': 'Admin123!'}), None))
        token = body['token']
        status, _ = parse_response(auth_mod.lambda_handler(
            make_event('POST', '/auth/change-password',
                       {'old_password': 'Admin123!', 'new_password': 'New1!'}, token=token), None))
        assert status == 200
        assert fake_ds.get_item('USER#admin', 'USER#admin')['force_password_change'] is False
        # Login with new password
        status, _ = parse_response(auth_mod.lambda_handler(
            make_event('POST', '/auth/login', {'username': 'admin', 'password': 'New1!'}), None))
        assert status == 200

    def test_wrong_old_password(self, fake_ds, admin_user):
        _, body = parse_response(auth_mod.lambda_handler(
            make_event('POST', '/auth/login', {'username': 'admin', 'password': 'Admin123!'}), None))
        status, _ = parse_response(auth_mod.lambda_handler(
            make_event('POST', '/auth/change-password',
                       {'old_password': 'wrong', 'new_password': 'x'}, token=body['token']), None))
        assert status == 401


class TestRouting:
    def test_options(self):
        status, _ = parse_response(auth_mod.lambda_handler(make_event('OPTIONS', '/auth/login'), None))
        assert status == 200

    def test_unknown_path(self):
        status, _ = parse_response(auth_mod.lambda_handler(make_event('POST', '/auth/unknown'), None))
        assert status == 404
