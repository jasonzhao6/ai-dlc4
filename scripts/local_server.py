#!/usr/bin/env python3
"""
Local dev server — runs the full app without AWS or SAM.
Uses DynamoDB Local + S3 Mock (Docker) and serves the React frontend.

Prerequisites:
    docker compose up -d
    pip install flask flask-cors
    cd frontend && REACT_APP_API_URL=http://localhost:5000 npm run build

Usage:
    python scripts/local_server.py
    Open http://localhost:5000
"""
import os, sys, json, hashlib, secrets, time

os.environ.update({
    'AWS_ACCESS_KEY_ID': 'fake', 'AWS_SECRET_ACCESS_KEY': 'fake',
    'AWS_DEFAULT_REGION': 'us-east-1', 'TABLE_NAME': 'test-table',
    'FILE_BUCKET': 'test-files', 'DYNAMODB_ENDPOINT': 'http://127.0.0.1:8033',
    'S3_ENDPOINT': 'http://127.0.0.1:9090',
})

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import boto3
from flask import Flask, request, send_from_directory
from flask_cors import CORS
from shared.data_store import DataStore
from shared.file_store import FileStore
from shared.session_validator import SessionValidator
from shared.access_control import AccessControl
import backend.auth.handler as auth_mod
import backend.users.handler as users_mod
import backend.folders.handler as folders_mod
import backend.files.handler as files_mod

# --- Init DDB table ---
ddb = boto3.client('dynamodb', endpoint_url='http://127.0.0.1:8033')
try:
    ddb.describe_table(TableName='test-table')
except ddb.exceptions.ResourceNotFoundException:
    ddb.create_table(
        TableName='test-table',
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1SK', 'AttributeType': 'S'},
        ],
        KeySchema=[{'AttributeName': 'PK', 'KeyType': 'HASH'}, {'AttributeName': 'SK', 'KeyType': 'RANGE'}],
        GlobalSecondaryIndexes=[{
            'IndexName': 'GSI1',
            'KeySchema': [{'AttributeName': 'GSI1PK', 'KeyType': 'HASH'}, {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}],
            'Projection': {'ProjectionType': 'ALL'},
        }],
        BillingMode='PAY_PER_REQUEST',
    )
    print('DynamoDB table created')

# --- Wire handlers ---
ds, fs = DataStore(), FileStore()
sv, ac = SessionValidator(ds), AccessControl(ds)
for mod in [auth_mod, users_mod, folders_mod, files_mod]:
    mod.ds, mod.sv = ds, sv
    if hasattr(mod, 'ac'): mod.ac = ac
    if hasattr(mod, 'fs'): mod.fs = fs

# --- Seed admin ---
if not ds.get_item('USER#admin', 'USER#admin'):
    salt = secrets.token_hex(16)
    ds.put_item({
        'PK': 'USER#admin', 'SK': 'USER#admin', 'username': 'admin',
        'password_hash': hashlib.sha256(f'{salt}Admin123!'.encode()).hexdigest(),
        'salt': salt, 'role': 'admin', 'force_password_change': True,
        'created_at': int(time.time()),
    })
    print('Admin seeded (admin / Admin123!)')

# --- Flask app ---
FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')
app = Flask(__name__, static_folder=FRONTEND, static_url_path='')
CORS(app)

def _event(path_params=None):
    return {
        'httpMethod': request.method, 'path': request.path,
        'headers': dict(request.headers), 'pathParameters': path_params,
        'body': request.get_data(as_text=True) or None,
    }

def _respond(resp):
    return app.response_class(resp.get('body', '{}'), status=resp.get('statusCode', 200), mimetype='application/json')

@app.route('/auth/<action>', methods=['POST', 'OPTIONS'])
def auth(action): return _respond(auth_mod.lambda_handler(_event(), None))

@app.route('/users', methods=['GET', 'POST', 'OPTIONS'])
def users(): return _respond(users_mod.lambda_handler(_event(), None))

@app.route('/users/<username>', methods=['PUT', 'DELETE', 'OPTIONS'])
def user(username): return _respond(users_mod.lambda_handler(_event({'username': username}), None))

@app.route('/folders', methods=['GET', 'POST', 'OPTIONS'])
def folders(): return _respond(folders_mod.lambda_handler(_event(), None))

@app.route('/folders/<folder_name>', methods=['PUT', 'DELETE', 'OPTIONS'])
def folder(folder_name): return _respond(folders_mod.lambda_handler(_event({'folder_name': folder_name}), None))

@app.route('/folders/<folder_name>/files', methods=['GET', 'OPTIONS'])
def list_files(folder_name): return _respond(files_mod.lambda_handler(_event({'folder_name': folder_name}), None))

@app.route('/folders/<folder_name>/files/upload', methods=['POST', 'OPTIONS'])
def upload(folder_name): return _respond(files_mod.lambda_handler(_event({'folder_name': folder_name}), None))

@app.route('/folders/<folder_name>/files/upload/complete', methods=['POST', 'OPTIONS'])
def upload_complete(folder_name): return _respond(files_mod.lambda_handler(_event({'folder_name': folder_name}), None))

@app.route('/folders/<folder_name>/files/<file_name>/download', methods=['POST', 'OPTIONS'])
def download(folder_name, file_name): return _respond(files_mod.lambda_handler(_event({'folder_name': folder_name, 'file_name': file_name}), None))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(FRONTEND, path)):
        return send_from_directory(FRONTEND, path)
    return send_from_directory(FRONTEND, 'index.html')

if __name__ == '__main__':
    print(f'\n  App running at http://localhost:5000')
    print(f'  Login: admin / Admin123!\n')
    app.run(port=5000, debug=True)
