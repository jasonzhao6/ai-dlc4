import os
import boto3
from boto3.dynamodb.conditions import Key, Attr


class DataStore:
    def __init__(self, table_name=None):
        self.table_name = table_name or os.environ['TABLE_NAME']
        self._dynamodb = boto3.resource('dynamodb')
        self._table = self._dynamodb.Table(self.table_name)

    def put_item(self, item):
        self._table.put_item(Item=item)

    def get_item(self, pk, sk):
        resp = self._table.get_item(Key={'PK': pk, 'SK': sk})
        return resp.get('Item')

    def query_by_pk(self, pk, sk_prefix=None):
        kce = Key('PK').eq(pk)
        if sk_prefix:
            kce = kce & Key('SK').begins_with(sk_prefix)
        resp = self._table.query(KeyConditionExpression=kce)
        return resp.get('Items', [])

    def query_gsi1(self, gsi1pk, gsi1sk_prefix=None):
        kce = Key('GSI1PK').eq(gsi1pk)
        if gsi1sk_prefix:
            kce = kce & Key('GSI1SK').begins_with(gsi1sk_prefix)
        resp = self._table.query(IndexName='GSI1', KeyConditionExpression=kce)
        return resp.get('Items', [])

    def delete_item(self, pk, sk):
        self._table.delete_item(Key={'PK': pk, 'SK': sk})

    def scan_by_pk_prefix(self, pk_prefix, sk_prefix=None):
        fe = Attr('PK').begins_with(pk_prefix)
        if sk_prefix:
            fe = fe & Attr('SK').begins_with(sk_prefix)
        resp = self._table.scan(FilterExpression=fe)
        items = resp.get('Items', [])
        while 'LastEvaluatedKey' in resp:
            resp = self._table.scan(FilterExpression=fe, ExclusiveStartKey=resp['LastEvaluatedKey'])
            items.extend(resp.get('Items', []))
        return items

    def batch_write(self, put_items=None, delete_keys=None):
        with self._table.batch_writer() as batch:
            for item in (put_items or []):
                batch.put_item(Item=item)
            for key in (delete_keys or []):
                batch.delete_item(Key=key)
