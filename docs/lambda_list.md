# lambda_list.py

## Purpose
Handles **listing, deleting, and saving corrections** for OCR extraction records stored in DynamoDB. This single Lambda serves three HTTP methods on the `/extractions` route.

## Trigger
- `GET /extractions` — list all extractions
- `DELETE /extractions?id=<id>` — delete a single extraction
- `PUT /extractions` — save corrected text for an extraction

All via API Gateway HTTP API.

## AWS Services Used
- **DynamoDB** — `scan`, `delete_item`, `update_item`
- **S3** — `head_object` to check file existence

## Environment Variables
| Variable     | Description |
|--------------|-------------|
| `TABLE_NAME` | DynamoDB table name (`ocr-extractions`) |
| `BUCKET`     | S3 bucket name |

## Method: GET (List Extractions)

### Input
None (no parameters required).

### Output
```json
{
  "extractions": [
    {
      "id": "uuid",
      "filename": "image.png",
      "s3_key": "r/turin/restaurant/id/image.png",
      "text": "extracted text...",
      "line_count": 12,
      "avg_confidence": 97.3,
      "corrected": false,
      "timestamp": "2026-02-10T12:00:00+00:00",
      "file_exists": true
    }
  ]
}
```

### Logic
1. Performs a full `table.scan()`.
2. Filters to keep only the most recent extraction per unique `filename` (removes duplicates).
3. Sorts items by `timestamp` descending (newest first).
4. Limits the result to the top 10 extractions.
5. Converts DynamoDB `Decimal` types: `line_count` → `int`, `avg_confidence` → `float`.
6. Defaults `corrected` to `False` if the field is missing.
7. For each item, checks if the S3 object exists using `head_object` on `s3_key`. Sets `file_exists` to `true` or `false`.
8. Returns the filtered, sorted, and limited list with file existence status.

---

## Method: DELETE (Delete Extraction)

### Input
| Parameter | Source | Required | Description |
|-----------|--------|----------|-------------|
| `id`      | Query string | Yes | The extraction ID to delete |

### Output
```json
{ "deleted": "uuid" }
```

### Logic
1. Reads `id` from query string parameters.
2. Returns 400 if missing.
3. Calls `table.delete_item(Key={'id': id})`.
4. Returns confirmation.

---

## Method: PUT (Save Corrected Text)

### Input
| Parameter | Source | Required | Description |
|-----------|--------|----------|-------------|
| `id`      | JSON body | Yes | The extraction ID to update |
| `text`    | JSON body | Yes | The corrected text content |

### Output
```json
{ "updated": "uuid" }
```

### Logic
1. Parses JSON body for `id` and `text`.
2. Returns 400 if either is missing.
3. Calls `table.update_item()` with:
   - Sets `text` to the new corrected value (uses `ExpressionAttributeNames` `#t` because `text` is a DynamoDB reserved word).
   - Sets `corrected = True` to flag the item as manually edited.
4. Returns confirmation.

## Critical Notes
- **`text` is a DynamoDB reserved word** — must use `ExpressionAttributeNames` (`#t`) in the UpdateExpression.
- HTTP method is detected from `event.requestContext.http.method`.

## IAM Permissions Required
- `dynamodb:Scan`, `dynamodb:GetItem`, `dynamodb:DeleteItem`, `dynamodb:UpdateItem` on the extractions table
- CloudWatch Logs

## Runtime
Python 3.11 | Timeout: 10s | Memory: 128MB
