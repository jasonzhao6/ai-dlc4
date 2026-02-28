"""Unit tests for folders Lambda handler."""
import os
import pytest

os.environ.setdefault('TABLE_NAME', 'test-table')
os.environ.setdefault('FILE_BUCKET', 'test-bucket')

from tests.helpers import (
    FakeDataStore, FakeFileStore, make_user_item, make_session_item,
    make_folder_item, make_assignment_item, make_file_item,
    parse_response, make_event,
)
import backend.folders.handler as folders_mod
from shared.session_validator import SessionValidator
from shared.access_control import AccessControl


@pytest.fixture(autouse=True)
def patch_folders(fake_ds, fake_fs):
    folders_mod.ds = fake_ds
    folders_mod.fs = fake_fs
    folders_mod.sv = SessionValidator(fake_ds)
    folders_mod.ac = AccessControl(fake_ds)
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


class TestCreateFolder:
    def test_success(self, fake_ds, admin_session):
        event = make_event('POST', '/folders', {'folder_name': 'docs'}, token=admin_session)
        status, _ = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 200
        assert fake_ds.get_item('FOLDER#docs', 'FOLDER#docs') is not None

    def test_duplicate(self, fake_ds, admin_session):
        fake_ds.put_item(make_folder_item('docs'))
        event = make_event('POST', '/folders', {'folder_name': 'docs'}, token=admin_session)
        status, _ = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 409

    def test_non_admin(self, viewer_session):
        event = make_event('POST', '/folders', {'folder_name': 'x'}, token=viewer_session)
        status, _ = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 403

    def test_empty_name(self, admin_session):
        event = make_event('POST', '/folders', {'folder_name': ''}, token=admin_session)
        status, _ = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 400


class TestListFolders:
    def test_admin_sees_all(self, fake_ds, admin_session):
        fake_ds.put_item(make_folder_item('docs'))
        fake_ds.put_item(make_folder_item('images'))
        event = make_event('GET', '/folders', token=admin_session)
        status, body = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 200
        names = [f['folder_name'] for f in body['folders']]
        assert 'docs' in names and 'images' in names

    def test_non_admin_sees_assigned_only(self, fake_ds, viewer_session):
        fake_ds.put_item(make_folder_item('docs'))
        fake_ds.put_item(make_folder_item('secret'))
        fake_ds.put_item(make_assignment_item('viewer1', 'docs'))
        event = make_event('GET', '/folders', token=viewer_session)
        status, body = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 200
        names = [f['folder_name'] for f in body['folders']]
        assert 'docs' in names
        assert 'secret' not in names


class TestRenameFolder:
    def test_rename_migrates_everything(self, fake_ds, fake_fs, admin_session):
        fake_ds.put_item(make_folder_item('old'))
        fake_ds.put_item(make_assignment_item('user1', 'old'))
        fake_ds.put_item(make_file_item('old', 'readme.txt'))
        fake_fs._objects['old/readme.txt'] = True

        event = make_event('PUT', '/folders/old', {'new_name': 'new'},
                           token=admin_session, path_params={'folder_name': 'old'})
        status, _ = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 200
        assert fake_ds.get_item('FOLDER#old', 'FOLDER#old') is None
        assert fake_ds.get_item('FOLDER#new', 'FOLDER#new') is not None
        assert fake_ds.get_item('USER#user1', 'FOLDER#new') is not None
        assert fake_ds.get_item('FOLDER#new', 'FILE#readme.txt') is not None
        assert 'new/readme.txt' in fake_fs._objects

    def test_nonexistent(self, admin_session):
        event = make_event('PUT', '/folders/ghost', {'new_name': 'x'},
                           token=admin_session, path_params={'folder_name': 'ghost'})
        status, _ = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 404


class TestDeleteFolder:
    def test_deletes_everything(self, fake_ds, fake_fs, admin_session):
        fake_ds.put_item(make_folder_item('docs'))
        fake_ds.put_item(make_assignment_item('user1', 'docs'))
        fake_ds.put_item(make_file_item('docs', 'file.txt'))
        fake_fs._objects['docs/file.txt'] = True

        event = make_event('DELETE', '/folders/docs', token=admin_session,
                           path_params={'folder_name': 'docs'})
        status, _ = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 200
        assert fake_ds.get_item('FOLDER#docs', 'FOLDER#docs') is None
        assert fake_ds.get_item('FOLDER#docs', 'FILE#file.txt') is None
        assert 'docs/file.txt' not in fake_fs._objects

    def test_nonexistent(self, admin_session):
        event = make_event('DELETE', '/folders/ghost', token=admin_session,
                           path_params={'folder_name': 'ghost'})
        status, _ = parse_response(folders_mod.lambda_handler(event, None))
        assert status == 404
