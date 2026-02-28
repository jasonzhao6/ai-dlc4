"""Unit tests for shared modules: AccessControl, SessionValidator, json_encoder."""
import json
import time
from decimal import Decimal

from shared.access_control import AccessControl
from shared.session_validator import SessionValidator
from shared.json_encoder import DecimalEncoder, api_response
from tests.helpers import FakeDataStore, make_user_item, make_session_item, make_assignment_item


class TestAccessControl:
    def setup_method(self):
        self.ds = FakeDataStore()
        self.ac = AccessControl(self.ds)

    def test_check_admin_true(self):
        assert self.ac.check_admin('admin') is True

    def test_check_admin_false_for_other_roles(self):
        for role in ('uploader', 'reader', 'viewer'):
            assert self.ac.check_admin(role) is False

    def test_admin_folder_access_without_assignment(self):
        assert self.ac.check_folder_access('admin', 'admin', 'any-folder') is True

    def test_non_admin_folder_access_with_assignment(self):
        self.ds.put_item(make_assignment_item('user1', 'docs'))
        assert self.ac.check_folder_access('user1', 'uploader', 'docs') is True

    def test_non_admin_folder_access_without_assignment(self):
        assert self.ac.check_folder_access('user1', 'uploader', 'docs') is False

    def test_permission_matrix_uploader(self):
        assert self.ac.check_file_action('uploader', 'view') is True
        assert self.ac.check_file_action('uploader', 'upload') is True
        assert self.ac.check_file_action('uploader', 'download') is True

    def test_permission_matrix_reader(self):
        assert self.ac.check_file_action('reader', 'view') is True
        assert self.ac.check_file_action('reader', 'upload') is False
        assert self.ac.check_file_action('reader', 'download') is True

    def test_permission_matrix_viewer(self):
        assert self.ac.check_file_action('viewer', 'view') is True
        assert self.ac.check_file_action('viewer', 'upload') is False
        assert self.ac.check_file_action('viewer', 'download') is False

    def test_authorize_combines_folder_and_action(self):
        self.ds.put_item(make_assignment_item('user1', 'docs'))
        assert self.ac.authorize('user1', 'reader', 'docs', 'download') is True
        assert self.ac.authorize('user1', 'reader', 'docs', 'upload') is False
        assert self.ac.authorize('user1', 'reader', 'other', 'download') is False


class TestSessionValidator:
    def setup_method(self):
        self.ds = FakeDataStore()
        self.sv = SessionValidator(self.ds)

    def test_valid_session(self):
        self.ds.put_item(make_session_item('tok123', 'admin', 'admin'))
        result = self.sv.validate({'headers': {'Authorization': 'tok123'}})
        assert result['username'] == 'admin'
        assert result['role'] == 'admin'

    def test_missing_token(self):
        assert self.sv.validate({'headers': {}}) is None

    def test_invalid_token(self):
        assert self.sv.validate({'headers': {'Authorization': 'bad'}}) is None

    def test_expired_session_deleted(self):
        self.ds.put_item(make_session_item('expired', 'admin', 'admin', ttl_offset=-100))
        assert self.sv.validate({'headers': {'Authorization': 'expired'}}) is None
        assert self.ds.get_item('SESSION#expired', 'SESSION#expired') is None

    def test_bearer_prefix_stripped(self):
        self.ds.put_item(make_session_item('tok456', 'user1', 'reader'))
        result = self.sv.validate({'headers': {'Authorization': 'Bearer tok456'}})
        assert result['username'] == 'user1'


class TestJsonEncoder:
    def test_decimal_int(self):
        assert json.dumps({'n': Decimal('42')}, cls=DecimalEncoder) == '{"n": 42}'

    def test_decimal_float(self):
        assert json.dumps({'n': Decimal('3.14')}, cls=DecimalEncoder) == '{"n": 3.14}'

    def test_api_response_structure(self):
        resp = api_response(200, {'ok': True})
        assert resp['statusCode'] == 200
        assert resp['headers']['Access-Control-Allow-Origin'] == '*'
        assert json.loads(resp['body']) == {'ok': True}
