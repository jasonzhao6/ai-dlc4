import json
import time

from shared.data_store import DataStore
from shared.file_store import FileStore
from shared.session_validator import SessionValidator
from shared.access_control import AccessControl
from shared.json_encoder import api_response

ds = DataStore()
fs = FileStore()
sv = SessionValidator(ds)
ac = AccessControl(ds)


def lambda_handler(event, context):
    method = event.get('httpMethod', '')
    path = event.get('path', '')

    if method == 'OPTIONS':
        return api_response(200, {})

    user_info = sv.validate(event)
    if not user_info:
        return api_response(401, {'error': 'Unauthorized'})

    if method == 'POST' and path == '/folders':
        return create_folder(event, user_info)
    elif method == 'GET' and path == '/folders':
        return list_folders(user_info)
    elif method == 'PUT' and path.startswith('/folders/'):
        return rename_folder(event, user_info)
    elif method == 'DELETE' and path.startswith('/folders/'):
        return delete_folder(event, user_info)

    return api_response(404, {'error': 'Not found'})


def create_folder(event, user_info):
    if not ac.check_admin(user_info['role']):
        return api_response(403, {'error': 'Admin only'})

    body = json.loads(event.get('body') or '{}')
    folder_name = body.get('folder_name', '').strip()

    if not folder_name:
        return api_response(400, {'error': 'folder_name required'})

    existing = ds.get_item(f'FOLDER#{folder_name}', f'FOLDER#{folder_name}')
    if existing:
        return api_response(409, {'error': 'Folder already exists'})

    ds.put_item({
        'PK': f'FOLDER#{folder_name}',
        'SK': f'FOLDER#{folder_name}',
        'folder_name': folder_name,
        's3_prefix': f'{folder_name}/',
        'created_at': int(time.time()),
    })

    return api_response(200, {'message': f'Folder {folder_name} created'})


def list_folders(user_info):
    if ac.check_admin(user_info['role']):
        folders = ds.scan_by_pk_prefix('FOLDER#', 'FOLDER#')
    else:
        assignments = ds.query_by_pk(f'USER#{user_info["username"]}', 'FOLDER#')
        folder_names = [a['folder_name'] for a in assignments]
        folders = []
        for fn in folder_names:
            f = ds.get_item(f'FOLDER#{fn}', f'FOLDER#{fn}')
            if f:
                folders.append(f)

    result = [{
        'folder_name': f['folder_name'],
        'created_at': f.get('created_at'),
    } for f in folders]

    return api_response(200, {'folders': result})


def rename_folder(event, user_info):
    if not ac.check_admin(user_info['role']):
        return api_response(403, {'error': 'Admin only'})

    old_name = event['pathParameters']['folder_name']
    body = json.loads(event.get('body') or '{}')
    new_name = body.get('new_name', '').strip()

    if not new_name:
        return api_response(400, {'error': 'new_name required'})

    old_folder = ds.get_item(f'FOLDER#{old_name}', f'FOLDER#{old_name}')
    if not old_folder:
        return api_response(404, {'error': 'Folder not found'})

    # Create new folder record
    ds.put_item({
        'PK': f'FOLDER#{new_name}',
        'SK': f'FOLDER#{new_name}',
        'folder_name': new_name,
        's3_prefix': f'{new_name}/',
        'created_at': old_folder.get('created_at', int(time.time())),
    })

    # Migrate folder assignments
    assignments = ds.query_gsi1(f'FOLDER#{old_name}', 'USER#')
    delete_keys = []
    put_items = []
    for a in assignments:
        delete_keys.append({'PK': a['PK'], 'SK': a['SK']})
        put_items.append({
            'PK': a['PK'],
            'SK': f'FOLDER#{new_name}',
            'GSI1PK': f'FOLDER#{new_name}',
            'GSI1SK': a['GSI1SK'],
            'username': a['username'],
            'folder_name': new_name,
            'assigned_at': a.get('assigned_at', int(time.time())),
        })

    # Migrate file metadata
    files = ds.query_by_pk(f'FOLDER#{old_name}', 'FILE#')
    for f in files:
        delete_keys.append({'PK': f['PK'], 'SK': f['SK']})
        put_items.append({
            'PK': f'FOLDER#{new_name}',
            'SK': f['SK'],
            'file_name': f['file_name'],
            'folder_name': new_name,
            's3_key': f'{new_name}/{f["file_name"]}',
            'size': f.get('size'),
            'uploaded_by': f.get('uploaded_by'),
            'uploaded_at': f.get('uploaded_at'),
        })

    if put_items or delete_keys:
        ds.batch_write(put_items=put_items, delete_keys=delete_keys)

    # Move S3 objects
    s3_keys = fs.list_objects_by_prefix(f'{old_name}/')
    for key in s3_keys:
        new_key = key.replace(f'{old_name}/', f'{new_name}/', 1)
        fs.copy_object(key, new_key)
        fs.delete_object(key)

    # Delete old folder record
    ds.delete_item(f'FOLDER#{old_name}', f'FOLDER#{old_name}')

    return api_response(200, {'message': f'Folder renamed to {new_name}'})


def delete_folder(event, user_info):
    if not ac.check_admin(user_info['role']):
        return api_response(403, {'error': 'Admin only'})

    folder_name = event['pathParameters']['folder_name']

    folder = ds.get_item(f'FOLDER#{folder_name}', f'FOLDER#{folder_name}')
    if not folder:
        return api_response(404, {'error': 'Folder not found'})

    # Delete S3 objects
    fs.delete_by_prefix(f'{folder_name}/')

    # Delete file metadata
    files = ds.query_by_pk(f'FOLDER#{folder_name}', 'FILE#')
    delete_keys = [{'PK': f['PK'], 'SK': f['SK']} for f in files]

    # Delete folder assignments
    assignments = ds.query_gsi1(f'FOLDER#{folder_name}', 'USER#')
    for a in assignments:
        delete_keys.append({'PK': a['PK'], 'SK': a['SK']})

    # Delete folder record
    delete_keys.append({'PK': f'FOLDER#{folder_name}', 'SK': f'FOLDER#{folder_name}'})

    ds.batch_write(delete_keys=delete_keys)

    return api_response(200, {'message': f'Folder {folder_name} deleted'})
