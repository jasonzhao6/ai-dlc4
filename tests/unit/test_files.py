"""Unit tests for files Lambda handler."""
import os
import pytest

os.environ.setdefault('TABLE_NAME', 'test-table')
os.environ.setdefault('FILE_BUCKET', 'test-bucket')

from tests.helpers import (
    FakeDataStore, FakeFileStore, make_user_item, make_session_item,
    make_folder_item, make_assignment_item, make_file_item,
    parse_response, make_event,
)
import backend.files.handler as files_mod
from shared.session_validator import SessionValidator
from shared.access_control import AccessControl


@pytest.fixture(autouse=True)
def patch_files(fake_ds, fake_fs):
    files_mod.ds = fake_ds
    files_mod.fs = fake_fs
    files_mod.sv = SessionValidator(fake_ds)
    files_mod.ac = AccessControl(fake_ds)
    yield


def setup_user(ds, username, role, token, folders=None):
    ds.put_item(make_user_item(username, 'pass', role))
    ds.put_item(make_session_item(token, username, role))
    for fn in (folders or []):
        ds.put_item(make_assignment_item(username, fn))


class TestListFiles:
    def test_assigned_user(self, fake_ds):
        setup_user(fake_ds, 'v1', 'viewer', 'v-tok', ['docs'])
        fake_ds.put_item(make_file_item('docs', 'a.txt'))
        fake_ds.put_item(make_file_item('docs', 'b.txt'))
        event = make_event('GET', '/folders/docs/files', token='v-tok',
                           path_params={'folder_name': 'docs'})
        status, body = parse_response(files_mod.lambda_handler(event, None))
        assert status == 200
        assert len(body['files']) == 2

    def test_unassigned_user(self, fake_ds):
        setup_user(fake_ds, 'v1', 'viewer', 'v-tok', [])
        event = make_event('GET', '/folders/secret/files', token='v-tok',
                           path_params={'folder_name': 'secret'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 403

    def test_admin_any_folder(self, fake_ds):
        setup_user(fake_ds, 'admin', 'admin', 'a-tok')
        fake_ds.put_item(make_file_item('any', 'x.txt'))
        event = make_event('GET', '/folders/any/files', token='a-tok',
                           path_params={'folder_name': 'any'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 200


class TestUpload:
    def test_uploader_gets_presigned_url(self, fake_ds):
        setup_user(fake_ds, 'up1', 'uploader', 'up-tok', ['docs'])
        event = make_event('POST', '/folders/docs/files/upload',
                           {'file_name': 'test.txt', 'file_size': 100},
                           token='up-tok', path_params={'folder_name': 'docs'})
        status, body = parse_response(files_mod.lambda_handler(event, None))
        assert status == 200
        assert 'upload_url' in body

    def test_reader_cannot_upload(self, fake_ds):
        setup_user(fake_ds, 'r1', 'reader', 'r-tok', ['docs'])
        event = make_event('POST', '/folders/docs/files/upload',
                           {'file_name': 'x.txt', 'file_size': 100},
                           token='r-tok', path_params={'folder_name': 'docs'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 403

    def test_viewer_cannot_upload(self, fake_ds):
        setup_user(fake_ds, 'v1', 'viewer', 'v-tok', ['docs'])
        event = make_event('POST', '/folders/docs/files/upload',
                           {'file_name': 'x.txt', 'file_size': 100},
                           token='v-tok', path_params={'folder_name': 'docs'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 403

    def test_file_too_large(self, fake_ds):
        setup_user(fake_ds, 'up1', 'uploader', 'up-tok', ['docs'])
        event = make_event('POST', '/folders/docs/files/upload',
                           {'file_name': 'big.bin', 'file_size': 2_000_000_000},
                           token='up-tok', path_params={'folder_name': 'docs'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 400

    def test_complete_records_metadata(self, fake_ds):
        setup_user(fake_ds, 'up1', 'uploader', 'up-tok', ['docs'])
        event = make_event('POST', '/folders/docs/files/upload/complete',
                           {'file_name': 'test.txt', 'file_size': 100},
                           token='up-tok', path_params={'folder_name': 'docs'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 200
        meta = fake_ds.get_item('FOLDER#docs', 'FILE#test.txt')
        assert meta is not None
        assert meta['uploaded_by'] == 'up1'

    def test_unassigned_folder(self, fake_ds):
        setup_user(fake_ds, 'up1', 'uploader', 'up-tok', [])
        event = make_event('POST', '/folders/secret/files/upload',
                           {'file_name': 'x.txt', 'file_size': 100},
                           token='up-tok', path_params={'folder_name': 'secret'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 403


class TestDownload:
    def test_reader_can_download(self, fake_ds):
        setup_user(fake_ds, 'r1', 'reader', 'r-tok', ['docs'])
        event = make_event('POST', '/folders/docs/files/test.txt/download', token='r-tok',
                           path_params={'folder_name': 'docs', 'file_name': 'test.txt'})
        status, body = parse_response(files_mod.lambda_handler(event, None))
        assert status == 200
        assert 'download_url' in body

    def test_viewer_cannot_download(self, fake_ds):
        setup_user(fake_ds, 'v1', 'viewer', 'v-tok', ['docs'])
        event = make_event('POST', '/folders/docs/files/test.txt/download', token='v-tok',
                           path_params={'folder_name': 'docs', 'file_name': 'test.txt'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 403

    def test_unassigned_folder(self, fake_ds):
        setup_user(fake_ds, 'r1', 'reader', 'r-tok', [])
        event = make_event('POST', '/folders/secret/files/x.txt/download', token='r-tok',
                           path_params={'folder_name': 'secret', 'file_name': 'x.txt'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 403


class TestNoAuth:
    def test_returns_401(self):
        event = make_event('GET', '/folders/docs/files', path_params={'folder_name': 'docs'})
        status, _ = parse_response(files_mod.lambda_handler(event, None))
        assert status == 401
