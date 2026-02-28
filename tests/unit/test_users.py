"""Unit tests for users Lambda handler."""
import os
import pytest

os.environ.setdefault('TABLE_NAME', 'test-table')
os.environ.setdefault('FILE_BUCKET', 'test-bucket')

from tests.helpers import (
    FakeDataStore, make_user_item, make_session_item, make_folder_item,
    make_assignment_item, parse_response, make_event,
)
import backend.users.handler as users_mod
from shared.session_validator import SessionValidator
from shared.access_control import AccessControl


@pytest.fixture(autouse=True)
def patch_users(fake_ds):
    users_mod.ds = fake_ds
    users_mod.sv = SessionValidator(fake_ds)
    users_mod.ac = AccessControl(fake_ds)
    yield


@pytest.fixture
def admin_session(fake_ds):
    fake_ds.put_item(make_user_item('admin', 'pass', 'admin'))
    fake_ds.put_item(make_session_item('admin-tok', 'admin', 'admin'))
    return 'admin-tok'


@pytest.fixture
def viewer_session(fake_ds):
    fake_ds.put_item(make_user_item('viewer1', 'pass', 'viewer'))
    fake_ds.put_item(make_session_item('viewer-tok', 'viewer1', 'viewer'))
    return 'viewer-tok'


class TestCreateUser:
    def test_success(self, fake_ds, admin_session):
        fake_ds.put_item(make_folder_item('docs'))
        event = make_event('POST', '/users', {
            'username': 'newuser', 'password': 'Pass1!', 'role': 'uploader',
            'folder_names': ['docs'],
        }, token=admin_session)
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 200
        assert fake_ds.get_item('USER#newuser', 'USER#newuser') is not None
        assert fake_ds.get_item('USER#newuser', 'FOLDER#docs') is not None

    def test_non_admin_forbidden(self, viewer_session):
        event = make_event('POST', '/users', {
            'username': 'x', 'password': 'x', 'role': 'viewer',
        }, token=viewer_session)
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 403

    def test_duplicate(self, fake_ds, admin_session):
        fake_ds.put_item(make_user_item('existing', 'pass', 'viewer'))
        event = make_event('POST', '/users', {
            'username': 'existing', 'password': 'x', 'role': 'viewer',
        }, token=admin_session)
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 409

    def test_invalid_role(self, admin_session):
        event = make_event('POST', '/users', {
            'username': 'x', 'password': 'x', 'role': 'superadmin',
        }, token=admin_session)
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 400

    def test_no_auth(self):
        event = make_event('POST', '/users', {'username': 'x', 'password': 'x', 'role': 'viewer'})
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 401


class TestListUsers:
    def test_admin_sees_all(self, fake_ds, admin_session):
        fake_ds.put_item(make_user_item('user1', 'p', 'reader'))
        event = make_event('GET', '/users', token=admin_session)
        status, body = parse_response(users_mod.lambda_handler(event, None))
        assert status == 200
        usernames = [u['username'] for u in body['users']]
        assert 'admin' in usernames and 'user1' in usernames

    def test_non_admin_forbidden(self, viewer_session):
        status, _ = parse_response(users_mod.lambda_handler(
            make_event('GET', '/users', token=viewer_session), None))
        assert status == 403


class TestUpdateUser:
    def test_update_role(self, fake_ds, admin_session):
        fake_ds.put_item(make_user_item('user1', 'p', 'viewer'))
        event = make_event('PUT', '/users/user1', {'role': 'reader'},
                           token=admin_session, path_params={'username': 'user1'})
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 200
        assert fake_ds.get_item('USER#user1', 'USER#user1')['role'] == 'reader'

    def test_update_folder_assignments(self, fake_ds, admin_session):
        fake_ds.put_item(make_user_item('user1', 'p', 'uploader'))
        fake_ds.put_item(make_assignment_item('user1', 'old-folder'))
        event = make_event('PUT', '/users/user1', {'folder_names': ['new-folder']},
                           token=admin_session, path_params={'username': 'user1'})
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 200
        assert fake_ds.get_item('USER#user1', 'FOLDER#old-folder') is None
        assert fake_ds.get_item('USER#user1', 'FOLDER#new-folder') is not None

    def test_nonexistent_user(self, admin_session):
        event = make_event('PUT', '/users/ghost', {'role': 'reader'},
                           token=admin_session, path_params={'username': 'ghost'})
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 404


class TestDeleteUser:
    def test_deletes_user_assignments_sessions(self, fake_ds, admin_session):
        fake_ds.put_item(make_user_item('user1', 'p', 'viewer'))
        fake_ds.put_item(make_assignment_item('user1', 'docs'))
        fake_ds.put_item(make_session_item('user1-tok', 'user1', 'viewer'))
        event = make_event('DELETE', '/users/user1', token=admin_session,
                           path_params={'username': 'user1'})
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 200
        assert fake_ds.get_item('USER#user1', 'USER#user1') is None
        assert fake_ds.get_item('USER#user1', 'FOLDER#docs') is None
        assert fake_ds.get_item('SESSION#user1-tok', 'SESSION#user1-tok') is None

    def test_nonexistent(self, admin_session):
        event = make_event('DELETE', '/users/ghost', token=admin_session,
                           path_params={'username': 'ghost'})
        status, _ = parse_response(users_mod.lambda_handler(event, None))
        assert status == 404
