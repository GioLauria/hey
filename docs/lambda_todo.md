# lambda_todo.py

To-Do list management Lambda function for the OCR web application.

## Purpose

Manages a simple To-Do list stored in DynamoDB, allowing users to create, read, update, and delete tasks.

## API Endpoints

### GET /todos
- **Purpose**: Retrieve all To-Do items
- **Response**: `{"todos": [{"id": "uuid", "text": "task description", "completed": false, "timestamp": "ISO8601"}]}`
- **Notes**: Items sorted by timestamp descending (newest first)

### POST /todos
- **Purpose**: Create a new To-Do item
- **Body**: `{"text": "task description", "completed": false}`
- **Response**: `{"id": "generated-uuid"}`
- **Notes**: Auto-generates UUID and timestamp

### PUT /todos
- **Purpose**: Update To-Do item completion status
- **Body**: `{"id": "uuid", "completed": true/false}`
- **Response**: `{"updated": "uuid"}`

### DELETE /todos?id=uuid
- **Purpose**: Delete a To-Do item
- **Response**: `{"deleted": "uuid"}`

## DynamoDB Table

**Table Name**: `ocr-todos`
- **Key**: `id` (String)
- **Attributes**:
  - `text` (String): The task description
  - `completed` (Boolean): Completion status
  - `timestamp` (String): ISO 8601 timestamp

## Environment Variables

- `TABLE_NAME`: DynamoDB table name (ocr-todos)

## IAM Permissions

- `dynamodb:GetItem`
- `dynamodb:PutItem`
- `dynamodb:UpdateItem`
- `dynamodb:DeleteItem`
- `dynamodb:Scan`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

## Error Handling

Returns appropriate HTTP status codes and error messages for invalid requests or DynamoDB failures.