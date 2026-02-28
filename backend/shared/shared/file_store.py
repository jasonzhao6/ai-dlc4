import os
import boto3
from botocore.config import Config


class FileStore:
    def __init__(self, bucket_name=None):
        self.bucket_name = bucket_name or os.environ['FILE_BUCKET']
        self._s3 = boto3.client('s3', config=Config(signature_version='s3v4'))

    def generate_presigned_put_url(self, s3_key, expiry_seconds=900):
        return self._s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': self.bucket_name, 'Key': s3_key},
            ExpiresIn=expiry_seconds,
        )

    def generate_presigned_get_url(self, s3_key, expiry_seconds=900):
        return self._s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': s3_key},
            ExpiresIn=expiry_seconds,
        )

    def copy_object(self, source_key, dest_key):
        self._s3.copy_object(
            Bucket=self.bucket_name,
            CopySource={'Bucket': self.bucket_name, 'Key': source_key},
            Key=dest_key,
        )

    def delete_object(self, s3_key):
        self._s3.delete_object(Bucket=self.bucket_name, Key=s3_key)

    def delete_by_prefix(self, prefix):
        keys = self.list_objects_by_prefix(prefix)
        for key in keys:
            self.delete_object(key)

    def list_objects_by_prefix(self, prefix):
        resp = self._s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        return [obj['Key'] for obj in resp.get('Contents', [])]
