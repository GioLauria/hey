# lambda_presign.py

## Purpose
Generates a **presigned S3 PUT URL** so the browser can upload images directly to the S3 bucket without needing AWS credentials on the client side. **Prevents duplicate uploads** by checking SHA256 hash against existing extractions before allowing upload.

## Trigger
`GET /presign?key=<filename>&hash=<sha256hash>` via API Gateway HTTP API.

## AWS Services Used
- **S3** — `generate_presigned_url` with `put_object` method
- **DynamoDB** — `scan` to check for existing hashes
- **RDS PostgreSQL** — Query restaurant details

## Environment Variables
| Variable | Description |
|----------|-------------|
| `BUCKET` | Name of the S3 bucket to upload to |
| `TABLE_NAME` | Name of the DynamoDB table for extractions |
| `DB_HOST` | PostgreSQL database host |

## IAM Permissions
Uses AWS managed policies:
- **AWSLambdaBasicExecutionRole**: CloudWatch Logs
- **AmazonS3FullAccess**: S3 operations
- **AmazonDynamoDBReadOnlyAccess**: DynamoDB scanning

## Input
| Parameter | Source | Required | Description |
|-----------|--------|----------|-------------|
| `key`     | Query string | Yes | The filename/key for the S3 object |
| `hash`    | Query string | Yes | SHA256 hash of the file content (computed client-side) |
| `restaurant` | Query string | Yes | The restaurant ID from the database |

## Output
```json
{ "url": "https://s3.eu-west-2.amazonaws.com/...", "s3_key": "r/1/filename.png" }
```
Or on duplicate:
```json
{ "error": "Image has already been processed" }
```

## Logic Flow
1. Creates an S3 client with **explicit regional endpoint** (`https://s3.eu-west-2.amazonaws.com`) and `s3v4` signature version.
2. Reads `key`, `hash`, and `restaurant` from `event.queryStringParameters`.
3. Returns 400 if `key`, `hash`, or `restaurant` is missing.
4. Queries PostgreSQL database to get restaurant details using the `restaurant` ID.
5. Scans DynamoDB extractions table for items with matching `hash`.
6. If duplicate found, returns 409 with error message.
7. If no duplicate, constructs S3 key as `"r/{restaurant_id}/{key}"`.
8. Calls `generate_presigned_url` for `put_object` with:
   - `ContentType: application/octet-stream`
   - `ExpiresIn: 300` seconds (5 minutes)
9. Returns the presigned URL and the full S3 key as JSON.

## Critical Notes
- **Must use regional endpoint** — the global `s3.amazonaws.com` endpoint causes CORS preflight failures on regional buckets.
- **Must use `s3v4` signature** — required for regional endpoints in `eu-west-2`.
- **No VPC attachment** — Runs outside VPC for cost optimization, connects to public RDS.
- The `ContentType` in the presigned URL must match the `Content-Type` header the browser sends when uploading, or S3 returns 403.
- **Hash check prevents duplicate processing** — saves costs by avoiding redundant Textract calls and storage.

## IAM Permissions Required
- `s3:PutObject` on the bucket
- `dynamodb:Scan` on the extractions table
- CloudWatch Logs (`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`)

## Runtime
Python 3.11 | Timeout: 5s | Memory: 128MB
