# lambda_s3_cleanup.py

## Purpose
Automatically removes records from the PostgreSQL `tblUploads` table when S3 objects are deleted by lifecycle policies. Maintains database consistency with S3 storage.

## Trigger
S3 bucket notification on `ObjectRemoved` events for objects under the `r/` prefix.

## AWS Services Used
- **S3** — Event notifications for object deletions
- **PostgreSQL** — Database record cleanup

## Environment Variables
None required.

## Input
S3 event notification JSON:
```json
{
  "Records": [{
    "eventName": "ObjectRemoved:*",
    "s3": {
      "object": {
        "key": "r/1/menu.jpg"
      }
    }
  }]
}
```

## Output
Logs cleanup operations to CloudWatch.

## Logic Flow
1. Receives S3 event notification for object deletion.
2. Parses the `s3_key` from the event.
3. Connects to PostgreSQL database.
4. Deletes the corresponding record from `tblUploads` where `S3_Path` matches the deleted key.
5. Logs the operation result.
6. Commits the transaction and closes the connection.

## Database Schema
| Table | Field | Type | Description |
|-------|-------|------|-------------|
| `tblUploads` | `ID` | SERIAL | Primary key |
| `tblUploads` | `Restaurant_ID` | INTEGER | Foreign key to tblRistoranti.ID |
| `tblUploads` | `S3_Path` | VARCHAR(500) | Full S3 object path |

## IAM Permissions Required
- CloudWatch Logs
- VPC access for PostgreSQL database connectivity

## Runtime
Python 3.11 | Timeout: 30s | Memory: 128MB