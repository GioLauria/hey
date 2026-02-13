import os
import json
import boto3
from botocore.config import Config
import pg8000

def lambda_handler(event, context):
    s3 = boto3.client(
        's3',
        region_name='eu-west-2',
        endpoint_url='https://s3.eu-west-2.amazonaws.com',
        config=Config(signature_version='s3v4')
    )
    bucket = os.environ['BUCKET']
    table_name = os.environ['TABLE_NAME']
    key = event.get('queryStringParameters', {}).get('key')
    hash_value = event.get('queryStringParameters', {}).get('hash')
    restaurant = event.get('queryStringParameters', {}).get('restaurant')
    if not key or not hash_value:
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Missing key or hash parameter'})
        }
    if not restaurant:
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Missing restaurant parameter'})
        }

    # Database connection
    conn = pg8000.connect(
        host=os.environ['DB_HOST'],
        port=int(os.environ.get('DB_PORT', 5432)),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'password123'),  # Use environment variable
        database=os.environ.get('DB_NAME', 'hey')
    )
    cursor = conn.cursor()

    # Query restaurant details
    cursor.execute('SELECT Name, City FROM tblRistoranti WHERE ID = %s', (restaurant,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {
            'statusCode': 404,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Restaurant not found'})
        }
    restaurant_name, city = row
    conn.close()

    s3_key = f"r/{restaurant}/{key}"  # Simplified S3 key with just restaurant_id/filename

    # Check for duplicate hash - temporarily removed for debugging
    # try:
    #     dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    #     table = dynamodb.Table(table_name)
    #     response = table.scan(
    #         FilterExpression=boto3.dynamodb.conditions.Attr('hash').eq(hash_value)
    #     )
    #     if response['Items']:
    #         return {
    #             'statusCode': 409,
    #             'headers': {'Access-Control-Allow-Origin': '*},
    #             'body': json.dumps({'error': 'Image has already been processed'})
    #     }
    # except Exception as e:
    #     # If DynamoDB check fails, log the error but allow upload
    #     print(f"DynamoDB check failed: {e}")
    #     pass

    url = s3.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': bucket,
            'Key': s3_key,
            'ContentType': 'application/octet-stream'
        },
        ExpiresIn=300
    )
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'url': url, 's3_key': s3_key})
    }
