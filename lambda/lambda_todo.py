import os
import json
import uuid
import boto3
from datetime import datetime, timezone

def lambda_handler(event, context):
    table_name = os.environ['TABLE_NAME']
    method = event['requestContext']['http']['method']
    path = event['requestContext']['http']['path']

    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    table = dynamodb.Table(table_name)

    if method == 'GET' and path == '/todos':
        try:
            response = table.scan()
            items = response.get('Items', [])
            # Sort by timestamp if available, otherwise by id
            items.sort(key=lambda x: x.get('timestamp', x.get('id', '')), reverse=True)
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'todos': items})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)})
            }

    elif method == 'POST' and path == '/todos':
        body = json.loads(event['body'])
        text = body['text']
        completed = body.get('completed', False)

        item_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            table.put_item(Item={
                'id': item_id,
                'text': text,
                'completed': completed,
                'timestamp': timestamp
            })
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'id': item_id})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)})
            }

    elif method == 'PUT' and path == '/todos':
        body = json.loads(event['body'])
        item_id = body['id']
        completed = body.get('completed')

        try:
            update_expression = 'SET completed = :c'
            expression_values = {':c': completed}
            update_params = {
                'Key': {'id': item_id},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values
            }

            if 'text' in body:
                update_expression += ', #t = :t'
                expression_values[':t'] = body['text']
                update_params['ExpressionAttributeNames'] = {'#t': 'text'}
                update_params['UpdateExpression'] = update_expression

            table.update_item(**update_params)
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'updated': item_id})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)})
            }

    elif method == 'DELETE' and path == '/todos':
        item_id = event.get('queryStringParameters', {}).get('id')
        if not item_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing id'})
            }
        try:
            table.delete_item(Key={'id': item_id})
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'deleted': item_id})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)})
            }

    return {
        'statusCode': 405,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'})
    }