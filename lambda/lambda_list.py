import os
import json
import boto3

def lambda_handler(event, context):
    table_name = os.environ['TABLE_NAME']
    bucket = os.environ['BUCKET']
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    table = dynamodb.Table(table_name)
    s3_client = boto3.client('s3', region_name='eu-west-2')

    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')

    # DELETE: remove a single extraction by id
    if method == 'DELETE':
        item_id = event.get('queryStringParameters', {}).get('id')
        if not item_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing id parameter'})
            }
        try:
            table.delete_item(Key={'id': item_id})
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)})
            }
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'deleted': item_id})
        }

    # PUT: save corrected text
    if method == 'PUT':
        try:
            body = json.loads(event.get('body', '{}'))
        except Exception:
            body = {}
        item_id = body.get('id')
        corrected_text = body.get('text')
        if not item_id or corrected_text is None:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing id or text'})
            }
        try:
            table.update_item(
                Key={'id': item_id},
                UpdateExpression='SET #t = :t, corrected = :c',
                ExpressionAttributeNames={'#t': 'text'},
                ExpressionAttributeValues={':t': corrected_text, ':c': True}
            )
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)})
            }
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'updated': item_id})
        }

    # GET: list all extractions
    try:
        response = table.scan()
        items = response.get('Items', [])
        # Sort by timestamp (most recent first) instead of filtering duplicates
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        items = items[:20]  # Limit to 20 most recent extractions
        for item in items:
            if 'line_count' in item:
                item['line_count'] = int(item['line_count'])
            if 'avg_confidence' in item:
                item['avg_confidence'] = float(item['avg_confidence'])
            if 'words' in item:
                # Convert Decimal confidence values to float for JSON serialization
                for word in item['words']:
                    if 'confidence' in word:
                        word['confidence'] = float(word['confidence'])
            if 'corrected' not in item:
                item['corrected'] = False
            # Check if S3 file exists
            s3_key = item.get('s3_key')
            if s3_key:
                try:
                    s3_client.head_object(Bucket=bucket, Key=s3_key)
                    item['file_exists'] = True
                except s3_client.exceptions.NoSuchKey:
                    item['file_exists'] = False
                except Exception:
                    item['file_exists'] = False  # Assume missing on error
            else:
                item['file_exists'] = False
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'extractions': items})
    }
