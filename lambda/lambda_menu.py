import os
import json
import uuid
import boto3
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
import base64

def lambda_handler(event, context):
    bucket = os.environ['BUCKET']
    table_name = os.environ['TABLE_NAME']
    method = event['requestContext']['http']['method']
    path = event['requestContext']['http']['path']

    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    table = dynamodb.Table(table_name)
    s3 = boto3.client('s3', region_name='eu-west-2')
    bedrock = boto3.client('bedrock-runtime', region_name='eu-west-2')

    if method == 'GET' and path == '/menu':
        extraction_id = event.get('queryStringParameters', {}).get('extraction_id')
        if not extraction_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing extraction_id'})
            }
        try:
            response = table.scan(
                FilterExpression=Attr('extraction_id').eq(extraction_id)
            )
            items = response.get('Items', [])
            items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            for item in items:
                if 'ptb' in item:
                    item['ptb'] = float(item['ptb'])
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'menu_items': items})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)})
            }

    elif method == 'POST' and path == '/menu':
        body = json.loads(event['body'])
        extraction_id = body['extraction_id']
        dish_name = body['dish_name']
        description = body['description']
        ingredients = body['ingredients']
        tts = body['tts']
        ptb = Decimal(str(body['ptb']))

        # Generate image
        prompt = f"A delicious, appetizing photo of {dish_name} dish made with {', '.join([f'{ing['quantity']} {ing['name']}' for ing in ingredients])}"
        try:
            response = bedrock.invoke_model(
                modelId='amazon.titan-image-generator-v1',
                body=json.dumps({
                    'taskType': 'TEXT_IMAGE',
                    'textToImageParams': {
                        'text': prompt
                    },
                    'imageGenerationConfig': {
                        'numberOfImages': 1,
                        'height': 512,
                        'width': 512,
                        'cfgScale': 8.0,
                        'seed': 42
                    }
                })
            )
            model_response = json.loads(response['body'].read())
            image_data = base64.b64decode(model_response['images'][0])

            item_id = str(uuid.uuid4())
            image_key = f'menu-images/{item_id}.png'
            s3.put_object(
                Bucket=bucket,
                Key=image_key,
                Body=image_data,
                ContentType='image/png'
            )

            timestamp = datetime.now(timezone.utc).isoformat()
            table.put_item(Item={
                'id': item_id,
                'extraction_id': extraction_id,
                'dish_name': dish_name,
                'description': description,
                'ingredients': ingredients,
                'tts': tts,
                'ptb': ptb,
                'image_key': image_key,
                'timestamp': timestamp
            })

            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'id': item_id, 'image_key': image_key})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)})
            }

    elif method == 'PUT' and path == '/menu':
        body = json.loads(event['body'])
        item_id = body['id']
        dish_name = body['dish_name']
        description = body['description']
        ingredients = body['ingredients']
        tts = body['tts']
        ptb = Decimal(str(body['ptb']))

        # Check if dish_name or ingredients changed to regenerate image
        try:
            current_item = table.get_item(Key={'id': item_id})['Item']
            regenerate = (current_item['dish_name'] != dish_name or
                          current_item['ingredients'] != ingredients)

            if regenerate:
                prompt = f"A delicious, appetizing photo of {dish_name} dish made with {', '.join([f'{ing['quantity']} {ing['name']}' for ing in ingredients])}"
                response = bedrock.invoke_model(
                    modelId='amazon.titan-image-generator-v1',
                    body=json.dumps({
                        'taskType': 'TEXT_IMAGE',
                        'textToImageParams': {
                            'text': prompt
                        },
                        'imageGenerationConfig': {
                            'numberOfImages': 1,
                            'height': 512,
                            'width': 512,
                            'cfgScale': 8.0,
                            'seed': 42
                        }
                    })
                )
                model_response = json.loads(response['body'].read())
                image_data = base64.b64decode(model_response['images'][0])
                image_key = f'menu-images/{item_id}.png'
                s3.put_object(
                    Bucket=bucket,
                    Key=image_key,
                    Body=image_data,
                    ContentType='image/png'
                )
            else:
                image_key = current_item['image_key']

            table.update_item(
                Key={'id': item_id},
                UpdateExpression='SET dish_name = :dn, description = :d, ingredients = :i, tts = :t, ptb = :p, image_key = :ik',
                ExpressionAttributeValues={
                    ':dn': dish_name,
                    ':d': description,
                    ':i': ingredients,
                    ':t': tts,
                    ':p': ptb,
                    ':ik': image_key
                }
            )

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

    elif method == 'DELETE' and path == '/menu':
        item_id = event.get('queryStringParameters', {}).get('id')
        if not item_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing id'})
            }
        try:
            item = table.get_item(Key={'id': item_id})['Item']
            table.delete_item(Key={'id': item_id})
            if 'image_key' in item:
                s3.delete_object(Bucket=bucket, Key=item['image_key'])
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