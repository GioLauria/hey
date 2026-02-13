import os
import json
import boto3
from datetime import datetime, timezone

def lambda_handler(event, context):
    method = event['requestContext']['http']['method']
    path = event['requestContext']['http']['path']

    if method == 'POST' and path == '/cache/invalidate':
        try:
            body = json.loads(event['body'])
            paths = body.get('paths', ['/*'])  # Default to invalidate all
            distribution_id = os.environ['CLOUDFRONT_DISTRIBUTION_ID']

            cloudfront = boto3.client('cloudfront', region_name='us-east-1')

            # Create invalidation
            response = cloudfront.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    'CallerReference': str(datetime.now(timezone.utc).timestamp()),
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    }
                }
            )

            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'message': 'Cache invalidation created',
                    'invalidation_id': response['Invalidation']['Id'],
                    'status': response['Invalidation']['Status']
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)})
            }

    elif method == 'GET' and path == '/cache/status':
        try:
            invalidation_id = event.get('queryStringParameters', {}).get('id')
            distribution_id = os.environ['CLOUDFRONT_DISTRIBUTION_ID']

            if not invalidation_id:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Missing invalidation_id parameter'})
                }

            cloudfront = boto3.client('cloudfront', region_name='us-east-1')
            response = cloudfront.get_invalidation(
                DistributionId=distribution_id,
                Id=invalidation_id
            )

            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'invalidation_id': response['Invalidation']['Id'],
                    'status': response['Invalidation']['Status'],
                    'create_time': response['Invalidation']['CreateTime'].isoformat() if response['Invalidation']['CreateTime'] else None
                })
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