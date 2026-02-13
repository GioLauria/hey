import json

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"message": "Hello from OCR Lambda!", "event": event})
    }