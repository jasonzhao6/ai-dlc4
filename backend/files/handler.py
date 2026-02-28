import json
import time

from shared.data_store import DataStore
from shared.file_store import FileStore
from shared.session_validator import SessionValidator
from shared.access_control import AccessControl
from shared.json_encoder import api_response

MAX_FILE_SIZE = 1_073_741_824  # 1GB
PRESIGNED_EXPIRY = 900  # 15 min

ds = DataStore()
fs = FileStore()
sv = SessionValidator(ds)
ac = AccessControl(ds)


def lambda_handler(event, context):
    method = event.get('httpMethod', '')
    path = event.get('path', '')
    params = event.get('pathParameters') or {}

    if method == 'OPTIONS':
        return api_response(200, {})

    user_info = sv.validate(event)
    if not user_info:
        return api_response(401, {'error': 'Unauthorized'})

    folder_name = params.get('folder_name', '')

    if method == 'GET' and path.endswith('/files'):
        return list_files(folder_name, user_info)
    elif method == 'POST' and path.endswith('/upload/complete'):
        return upload_complete(event, folder_name, user_info)
    elif method == 'POST' and path.endswith('/upload'):
        return upload_request(event, folder_name, user_info)
    elif method == 'POST' and '/download' in path:
        file_name = params.get('file_name', '')
        return download_request(folder_name, file_name, user_info)

    return api_response(404, {'error': 'Not found'})


def list_files(folder_name, user_info):
    if not ac.authorize(user_info['username'], user_info['role'], folder_name, 'view'):
        return api_response(403, {'error': 'Access denied'})

    files = ds.query_by_pk(f'FOLDER#{folder_name}', 'FILE#')
    result = [{
        'file_name': f['file_name'],
        'size': f.get('size'),
        'uploaded_by': f.get('uploaded_by'),
        'uploaded_at': f.get('uploaded_at'),
    } for f in files]

    return api_response(200, {'files': result})


def upload_request(event, folder_name, user_info):
    if not ac.authorize(user_info['username'], user_info['role'], folder_name, 'upload'):
        return api_response(403, {'error': 'Access denied'})

    body = json.loads(event.get('body') or '{}')
    file_name = body.get('file_name', '').strip()
    file_size = body.get('file_size', 0)

    if not file_name:
        return api_response(400, {'error': 'file_name required'})
    if file_size > MAX_FILE_SIZE:
        return api_response(400, {'error': f'File size exceeds maximum of {MAX_FILE_SIZE} bytes (1GB)'})

    s3_key = f'{folder_name}/{file_name}'
    upload_url = fs.generate_presigned_put_url(s3_key, PRESIGNED_EXPIRY)

    return api_response(200, {'upload_url': upload_url, 's3_key': s3_key})


def upload_complete(event, folder_name, user_info):
    if not ac.authorize(user_info['username'], user_info['role'], folder_name, 'upload'):
        return api_response(403, {'error': 'Access denied'})

    body = json.loads(event.get('body') or '{}')
    file_name = body.get('file_name', '').strip()
    file_size = body.get('file_size', 0)

    if not file_name:
        return api_response(400, {'error': 'file_name required'})

    ds.put_item({
        'PK': f'FOLDER#{folder_name}',
        'SK': f'FILE#{file_name}',
        'file_name': file_name,
        'folder_name': folder_name,
        's3_key': f'{folder_name}/{file_name}',
        'size': file_size,
        'uploaded_by': user_info['username'],
        'uploaded_at': int(time.time()),
    })

    return api_response(200, {'message': f'File {file_name} metadata recorded'})


def download_request(folder_name, file_name, user_info):
    if not ac.authorize(user_info['username'], user_info['role'], folder_name, 'download'):
        return api_response(403, {'error': 'Access denied'})

    s3_key = f'{folder_name}/{file_name}'
    download_url = fs.generate_presigned_get_url(s3_key, PRESIGNED_EXPIRY)

    return api_response(200, {'download_url': download_url})
