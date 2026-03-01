# lambda_cache.py

CloudFront cache invalidation Lambda function for the OCR web application.

## Purpose

Provides API endpoints to invalidate CloudFront cache distributions, allowing immediate cache refresh functionality.

## API Endpoints

### POST /cache/invalidate
- **Purpose**: Create a CloudFront invalidation for specified paths
- **Body**: `{"paths": ["/path1", "/path2"]}` (optional, defaults to ["/*"])
- **Response**: `{"message": "Cache invalidation created", "invalidation_id": "I123456789", "status": "InProgress"}`
- **Notes**: Invalidates all paths by default if no paths specified

### GET /cache/status?id=I123456789
- **Purpose**: Check the status of a CloudFront invalidation
- **Response**: `{"invalidation_id": "I123456789", "status": "Completed", "create_time": "2026-02-11T10:05:25.309000+00:00"}`
- **Notes**: Status can be "InProgress", "Completed", or "Failed"

## CloudFront Integration

- Uses the CloudFront distribution ID from environment variables
- Creates invalidations for specified paths
- Returns invalidation ID for status tracking

## Environment Variables

- `CLOUDFRONT_DISTRIBUTION_ID`: CloudFront distribution ID to invalidate

## IAM Permissions

- `cloudfront:CreateInvalidation`
- `cloudfront:GetInvalidation`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

## Error Handling

Returns appropriate HTTP status codes and error messages for:
- Invalid invalidation IDs
- CloudFront API failures
- Missing environment variables