# lambda_menu.py — Menu Management Lambda with AI Image Generation

This Lambda function handles CRUD operations for restaurant menu items derived from OCR extractions. It uses Amazon Bedrock to generate AI-powered dish images and stores structured menu data in DynamoDB.

## Functionality

- **GET /menu**: Retrieves menu items for a specific extraction ID, sorted by timestamp descending. Converts Decimal PTB to float for JSON serialization. Returns error details on failure.
- **POST /menu**: Creates a new menu item with AI-generated image using Titan Image Generator. Prompt includes dish name and ingredients for realistic food photography. Returns error details on failure.
- **PUT /menu**: Updates an existing menu item. Regenerates image only if dish name or ingredients change to avoid unnecessary API calls. Returns error details on failure.
- **DELETE /menu**: Removes menu item and associated S3 image object. Returns error details on failure.

## Key Features

- **AI Image Generation**: Leverages Bedrock's Titan model for high-quality, 512x512 food images based on textual descriptions.
- **Efficient Updates**: Conditional image regeneration prevents redundant Bedrock invocations.
- **Data Integrity**: Uses DynamoDB Decimal for price storage, proper error handling for missing parameters.
- **CORS Compliance**: All responses include Access-Control-Allow-Origin header for web integration.

## Environment Variables

- `BUCKET`: S3 bucket name for storing generated images under `menu-images/` prefix.
- `TABLE_NAME`: DynamoDB table name (`menu-items`).

## IAM Permissions

- `bedrock:InvokeModel` on `amazon.titan-image-generator-v1`
- `s3:PutObject` and `s3:DeleteObject` on the bucket
- `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:DeleteItem`, `dynamodb:Scan` on the menu-items table
- CloudWatch Logs for monitoring

## Dependencies

- boto3 for AWS service interactions
- base64 for image decoding
- json for request/response handling
- uuid for unique item IDs
- datetime for timestamps
- decimal for price handling